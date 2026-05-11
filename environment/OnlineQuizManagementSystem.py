# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Optional, Any



# Represents a unique quiz question and its associated metadata.
class QuestionInfo(TypedDict):
    question_id: str
    content: str
    subject: str
    difficulty: str
    question_type: str
    active: bool  # For API filtering

# Represents an answer option for a question, with a flag for correctness.
class AnswerInfo(TypedDict):
    answer_id: str
    question_id: str
    answer_text: str
    is_correct: bool
    active: bool  # For API filtering

# Represents a set of questions grouped as a single quiz.
class QuizInfo(TypedDict):
    quiz_id: str
    quiz_title: str
    description: str
    subject: str
    difficulty: str
    questions: List[str]  # List of question_ids

# Represents a user in the system.
class UserInfo(TypedDict):
    _id: str
    name: str
    email: str

# Represents a user's attempt at a quiz.
class AttemptInfo(TypedDict):
    attempt_id: str
    user_id: str
    quiz_id: str
    timestamp: str  # Could also be float (unix timestamp)
    score: float
    responses: List[Dict[str, Any]]  # e.g., list of {"question_id": ..., "answer_id": ...}

class _GeneratedEnvImpl:
    def __init__(self):
        # Questions: {question_id: QuestionInfo}
        self.questions: Dict[str, QuestionInfo] = {}

        # Answers: {answer_id: AnswerInfo}
        self.answers: Dict[str, AnswerInfo] = {}

        # Quizzes: {quiz_id: QuizInfo}
        self.quizzes: Dict[str, QuizInfo] = {}

        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Attempts: {attempt_id: AttemptInfo}
        self.attempts: Dict[str, AttemptInfo] = {}

        # --- Constraints ---
        # - Each question must have at least one correct and active answer.
        # - Only questions and answers marked as 'active' should be returned via the API.
        # - Questions can be filtered by subject and difficulty.
        # - A question can belong to one or more quizzes (via quizzes[].questions lists).
        # - Questions:Answers is one-to-many (answers reference question_id).

    def get_questions_by_subject_and_difficulty(self, subject: str, difficulty: str) -> dict:
        """
        Retrieve all active questions filtered by subject and difficulty.

        Args:
            subject (str): The subject to filter questions by.
            difficulty (str): The difficulty level to filter questions by.

        Returns:
            dict: {
                "success": True,
                "data": List[QuestionInfo]
            }
            List is empty if no matching questions found.

        Constraints:
            - Only questions with active == True are included.
            - Match subject and difficulty exactly (case-sensitive).
        """
        filtered_questions = [
            q for q in self.questions.values()
            if q.get("active", False)
               and q.get("subject") == subject
               and q.get("difficulty") == difficulty
        ]
        return {
            "success": True,
            "data": filtered_questions
        }

    def get_active_question_by_id(self, question_id: str) -> dict:
        """
        Retrieve an active question by its question_id.

        Args:
            question_id (str): The ID of the question to retrieve.

        Returns:
            dict: On success,
                {
                    "success": True,
                    "data": QuestionInfo
                }
                On failure,
                {
                    "success": False,
                    "error": "Question not found or inactive"
                }

        Constraints:
            - Only return the question if it is marked as 'active'.
        """
        question = self.questions.get(question_id)
        if not question or not question.get("active", False):
            return { "success": False, "error": "Question not found or inactive" }

        return { "success": True, "data": question }

    def get_answers_by_question_id(self, question_id: str) -> dict:
        """
        Retrieve all active answers for a given question.

        Args:
            question_id (str): The unique identifier of the question.

        Returns:
            dict: 
              - If successful: {"success": True, "data": List[AnswerInfo] }
                (list may be empty if no active answers)
              - If unsuccessful: {"success": False, "error": str}

        Constraints:
            - Only answers with 'active' == True are returned.
            - The referenced question must exist and be active.
        """
        question = self.questions.get(question_id)
        if not question or not question.get("active", False):
            return {"success": False, "error": "Question does not exist or is not active"}

        active_answers = [
            answer
            for answer in self.answers.values()
            if answer["question_id"] == question_id and answer.get("active", False)
        ]
        return {"success": True, "data": active_answers}

    def get_correct_answers_by_question_id(self, question_id: str) -> dict:
        """
        Retrieve all active and correct answers for the specified question.

        Args:
            question_id (str): Unique identifier of the question.

        Returns:
            dict:
                - On success: {
                    "success": True,
                    "data": List[AnswerInfo],  # active & correct answers for the question
                  }
                - On failure (invalid question_id): {
                    "success": False,
                    "error": "Question not found"
                  }

        Constraints:
            - Only answers where is_correct == True and active == True are returned.
            - If the question_id does not exist in the database, return an error.
        """
        if question_id not in self.questions:
            return { "success": False, "error": "Question not found" }

        matches = [
            answer
            for answer in self.answers.values()
            if answer["question_id"] == question_id and answer["is_correct"] and answer["active"]
        ]

        return { "success": True, "data": matches }

    def list_quizzes(self) -> dict:
        """
        List all quizzes currently in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[QuizInfo]  # List of all quizzes (can be empty if no quizzes exist)
            }

        Notes:
            - This method returns all quizzes regardless of contents.
            - No error is returned if no quizzes exist; data will simply be an empty list.
        """
        all_quizzes = list(self.quizzes.values())
        return {
            "success": True,
            "data": all_quizzes
        }

    def get_quiz_by_id(self, quiz_id: str) -> dict:
        """
        Retrieve all metadata and active questions for a specific quiz.

        Args:
            quiz_id (str): Unique identifier of the quiz.

        Returns:
            dict:
                - success: True, data: {
                    "quiz": QuizInfo,
                    "questions": List[QuestionInfo]  # Only active questions,
                }
                - success: False, error: error description

        Constraints:
            - Only questions marked as 'active' are included.
            - If the quiz does not exist, return error.
        """
        quiz = self.quizzes.get(quiz_id)
        if not quiz:
            return { "success": False, "error": "Quiz not found" }

        active_questions = []
        for qid in quiz.get("questions", []):
            question = self.questions.get(qid)
            if question and question.get("active", False):
                active_questions.append(question)

        return {
            "success": True,
            "data": {
                "quiz": quiz,
                "questions": active_questions
            }
        }

    def get_questions_in_quiz(self, quiz_id: str) -> dict:
        """
        Retrieve all active questions belonging to a given quiz.

        Args:
            quiz_id (str): The ID of the quiz.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[QuestionInfo]  # List of active questions in the quiz (may be empty).
                }
                Or, on error:
                {
                    "success": False,
                    "error": str  # 'Quiz not found'
                }

        Constraints:
            - Only active questions (question['active'] == True) are returned.
            - If quiz does not exist, return error.
            - If quiz's question list includes question IDs not present in the questions dict, skip them.
        """
        quiz = self.quizzes.get(quiz_id)
        if not quiz:
            return { "success": False, "error": "Quiz not found" }
        result = []
        for qid in quiz.get("questions", []):
            question = self.questions.get(qid)
            if question and question.get("active", False):
                result.append(question)
        return { "success": True, "data": result }

    def get_attempts_by_user_id(self, user_id: str) -> dict:
        """
        List all quiz attempts for a specific user.

        Args:
            user_id (str): The user's unique identifier.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": List[AttemptInfo],  # May be empty if the user has no attempts
                    }
                - On error:
                    {
                        "success": False,
                        "error": "User does not exist"
                    }

        Constraints:
            - user_id must exist in self.users.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        user_attempts = [
            attempt for attempt in self.attempts.values()
            if attempt["user_id"] == user_id
        ]

        return { "success": True, "data": user_attempts }

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user information by user ID.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo  # User information dictionary
            }
            or
            {
                "success": False,
                "error": "User not found"
            }

        Constraints:
            - The user ID must exist in the system.
        """
        user_info = self.users.get(user_id)
        if user_info is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user_info }

    def get_attempt_detail(self, attempt_id: str) -> dict:
        """
        Retrieve detailed information for a specific attempt, including score, responses, user, and quiz info.

        Args:
            attempt_id (str): The unique identifier for the attempt.

        Returns:
            dict: 
                - On success: 
                    { "success": True, "data": AttemptInfo }
                - On failure: 
                    { "success": False, "error": "Attempt does not exist" }

        Constraints:
            - The attempt_id must exist in the system.
        """
        attempt = self.attempts.get(attempt_id)
        if not attempt:
            return { "success": False, "error": "Attempt does not exist" }
        return { "success": True, "data": attempt }

    def activate_question(self, question_id: str) -> dict:
        """
        Sets the 'active' status of a question to True.

        Args:
            question_id (str): The ID of the question to activate.

        Returns:
            dict: {
                "success": True,
                "message": "Question <question_id> marked as active."
            }
            or
            {
                "success": False,
                "error": str  # Description of why it failed.
            }

        Constraints:
            - The question must exist in the system.
            - Idempotent: If already active, still returns success.
        """
        question = self.questions.get(question_id)
        if question is None:
            return { "success": False, "error": "Question not found." }

        question["active"] = True
        return { "success": True, "message": f"Question {question_id} marked as active." }

    def deactivate_question(self, question_id: str) -> dict:
        """
        Set a question's 'active' status to False.

        Args:
            question_id (str): The unique identifier of the question to deactivate.

        Returns:
            dict: {
                "success": True,
                "message": "Question <question_id> deactivated."
            }
            or
            {
                "success": False,
                "error": "Question not found."
            }

        Constraints:
            - Only questions that exist may be deactivated.
            - Setting 'active' to False is idempotent; if already False, remains False.
            - Does not cascade deactivation to answers or quizzes (handled separately).
        """
        question = self.questions.get(question_id)
        if not question:
            return { "success": False, "error": "Question not found." }
    
        if not question.get("active", False):
            # Already inactive; considered successful (idempotent)
            question["active"] = False
            return { "success": True, "message": f"Question {question_id} is already deactivated." }
    
        question["active"] = False
        return { "success": True, "message": f"Question {question_id} deactivated." }

    def activate_answer(self, answer_id: str) -> dict:
        """
        Set an answer's 'active' status to True.

        Args:
            answer_id (str): The unique ID of the answer to activate.

        Returns:
            dict: {
                "success": True,
                "message": "Answer <id> activated"
            }
            OR
            {
                "success": False,
                "error": "Answer not found"
            }
        Constraints:
            - The answer must exist in the system.
            - The operation is idempotent (activating an already active answer is a success).
        """
        answer = self.answers.get(answer_id)
        if answer is None:
            return { "success": False, "error": "Answer not found" }
        if answer["active"]:
            # Already active -- treat idempotently.
            return { "success": True, "message": f"Answer {answer_id} activated" }
        answer["active"] = True
        return { "success": True, "message": f"Answer {answer_id} activated" }

    def deactivate_answer(self, answer_id: str) -> dict:
        """
        Set an answer's 'active' status to False.
    
        Args:
            answer_id (str): The unique identifier of the answer to deactivate.

        Returns:
            dict: Success/failure and message.
                On success: { "success": True, "message": "Answer <id> deactivated." }
                On failure: { "success": False, "error": "reason for failure" }

        Constraints:
            - Only set 'active' to False if this would not violate: 
              "Each question must have at least one correct and active answer."
            - If answer_id not present, return error.
            - If already inactive, treat as successful operation but note in message.
        """
        # Check if the answer exists
        if answer_id not in self.answers:
            return { "success": False, "error": "Answer does not exist." }
    
        answer = self.answers[answer_id]
        if not answer["active"]:
            return { "success": True, "message": f"Answer {answer_id} is already deactivated." }
    
        question_id = answer["question_id"]

        # If this answer is correct, ensure deactivation won't leave the question with no correct/active answer
        if answer.get("is_correct", False):
            num_correct_active = sum(
                1 for ans in self.answers.values()
                if ans["question_id"] == question_id and ans["active"] and ans["is_correct"] and ans["answer_id"] != answer_id
            )
            if num_correct_active == 0:
                return {
                    "success": False,
                    "error": "Cannot deactivate this answer: each question must have at least one correct and active answer."
                }

        # All checks passed, deactivate the answer
        self.answers[answer_id]["active"] = False
        return { "success": True, "message": f"Answer {answer_id} deactivated." }

    def add_question(
        self,
        question_id: str,
        content: str,
        subject: str,
        difficulty: str,
        question_type: str,
        active: bool = True
    ) -> dict:
        """
        Add a new question to the system.

        Args:
            question_id (str): Unique identifier for the question.
            content (str): The question text.
            subject (str): Subject category (e.g., "math", "history").
            difficulty (str): Difficulty level ("easy", "medium", "hard", etc.).
            question_type (str): The type of the question ("multiple-choice", "true/false", etc.).
            active (bool): Whether the question is currently active/visible (default: True).

        Returns:
            dict: {
                "success": True,
                "message": "Question added successfully."
            }
            or
            {
                "success": False,
                "error": "reason for failure"
            }

        Constraints:
            - question_id must be unique (no existing question with same id).
        """
        if not all([question_id, content, subject, difficulty, question_type]):
            return {"success": False, "error": "All required fields must be provided."}
        if question_id in self.questions:
            return {"success": False, "error": "Question ID already exists."}

        self.questions[question_id] = {
            "question_id": question_id,
            "content": content,
            "subject": subject,
            "difficulty": difficulty,
            "question_type": question_type,
            "active": active,
        }

        return {"success": True, "message": "Question added successfully."}

    def add_answer(
        self,
        answer_id: str,
        question_id: str,
        answer_text: str,
        is_correct: bool,
        active: bool = True
    ) -> dict:
        """
        Add a new answer option to a question.

        Args:
            answer_id (str): Unique ID for the new answer.
            question_id (str): The ID of the question this answer is for.
            answer_text (str): The answer option text.
            is_correct (bool): Whether this answer is correct.
            active (bool): Whether this answer is active (default True).
    
        Returns:
            dict: {
                "success": True,
                "message": "Answer added to question <question_id>."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - answer_id must be unique.
            - question_id must exist and be active.
            - answer_text must not be empty.
            - is_correct should be bool.
        """
        if not isinstance(answer_id, str) or not answer_id:
            return { "success": False, "error": "Invalid or missing answer_id." }
        if not isinstance(question_id, str) or not question_id:
            return { "success": False, "error": "Invalid or missing question_id." }
        if answer_id in self.answers:
            return { "success": False, "error": "Answer ID already exists." }
        q = self.questions.get(question_id)
        if not q:
            return { "success": False, "error": "Question ID does not exist." }
        if not q.get("active", True):
            return { "success": False, "error": "Question is not active." }
        if not isinstance(answer_text, str) or not answer_text.strip():
            return { "success": False, "error": "Answer text cannot be empty." }
        if not isinstance(is_correct, bool):
            return { "success": False, "error": "is_correct must be a boolean." }
        if not isinstance(active, bool):
            return { "success": False, "error": "active must be a boolean." }

        self.answers[answer_id] = {
            "answer_id": answer_id,
            "question_id": question_id,
            "answer_text": answer_text,
            "is_correct": is_correct,
            "active": active
        }

        return { "success": True, "message": f"Answer added to question {question_id}." }

    def update_question_content(
        self,
        question_id: str,
        content: Optional[str] = None,
        subject: Optional[str] = None,
        difficulty: Optional[str] = None,
        question_type: Optional[str] = None
    ) -> dict:
        """
        Modify the content or metadata (subject, difficulty, question_type) of a specific question.

        Args:
            question_id (str): The ID of the question to update.
            content (Optional[str]): New content for the question.
            subject (Optional[str]): New subject/category for the question.
            difficulty (Optional[str]): New difficulty level for the question.
            question_type (Optional[str]): New question type (e.g., 'multiple-choice', etc.).

        Returns:
            dict: 
                Success: { "success": True, "message": "Question <id> updated." }
                Failure: { "success": False, "error": "reason" }

        Constraints:
            - Question must exist.
            - At least one updatable field (other than question_id) must be provided.
            - Only updates provided (non-None) fields.
        """
        question = self.questions.get(question_id)
        if question is None:
            return { "success": False, "error": "Question not found." }

        fields_to_update = {}
        if content is not None:
            fields_to_update["content"] = content
        if subject is not None:
            fields_to_update["subject"] = subject
        if difficulty is not None:
            fields_to_update["difficulty"] = difficulty
        if question_type is not None:
            fields_to_update["question_type"] = question_type

        if not fields_to_update:
            return { "success": False, "error": "No fields to update." }

        for k, v in fields_to_update.items():
            self.questions[question_id][k] = v

        return { "success": True, "message": f"Question {question_id} updated." }

    def update_answer_text(self, answer_id: str, answer_text: Optional[str] = None, is_correct: Optional[bool] = None) -> dict:
        """
        Modify the text and/or correctness of an answer.

        Args:
            answer_id (str): The ID of the answer to update.
            answer_text (Optional[str]): If provided, the new answer text.
            is_correct (Optional[bool]): If provided, the new correctness flag.

        Returns:
            dict: {
                "success": True,
                "message": "Answer updated successfully"
            }
            OR
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - The answer must exist.
            - If is_correct is updated to False, the parent question must still have at least one correct AND active answer.
        """
        answer = self.answers.get(answer_id)
        if not answer:
            return {"success": False, "error": "Answer not found"}

        updated = False

        if answer_text is not None:
            answer["answer_text"] = answer_text
            updated = True

        if is_correct is not None and is_correct != answer["is_correct"]:
            # If changing from True to False, check the constraint.
            if is_correct is False and answer["is_correct"] is True:
                qid = answer["question_id"]
                # Count other correct and active answers
                count = 0
                for a in self.answers.values():
                    if (
                        a["question_id"] == qid
                        and a["active"]
                        and a["is_correct"]
                        and a["answer_id"] != answer_id
                    ):
                        count += 1
                if count == 0:
                    return {
                        "success": False,
                        "error": "Each question must have at least one correct and active answer"
                    }
            # Allowed. Update.
            answer["is_correct"] = is_correct
            updated = True

        if not updated:
            return {"success": False, "error": "No update fields provided or nothing changed"}

        return {"success": True, "message": "Answer updated successfully"}

    def create_quiz(
        self,
        quiz_id: str,
        quiz_title: str,
        description: str,
        subject: str,
        difficulty: str,
        questions: list
    ) -> dict:
        """
        Create a new quiz with a group of specified question_ids.

        Args:
            quiz_id (str): Unique identifier for the new quiz.
            quiz_title (str): Human-readable quiz name.
            description (str): Description of the quiz.
            subject (str): Subject/category for the quiz.
            difficulty (str): Difficulty label of the quiz.
            questions (List[str]): List of question_ids to be included in the quiz.

        Returns:
            dict: {
                "success": True,
                "message": "Quiz <quiz_id> created successfully."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - quiz_id must be unique.
            - Every question_id must exist and be active.
            - questions list must not be empty.
        """
        if not quiz_id or not isinstance(quiz_id, str):
            return {"success": False, "error": "Quiz ID must be a non-empty string."}

        if quiz_id in self.quizzes:
            return {"success": False, "error": f"Quiz ID '{quiz_id}' already exists."}

        if not isinstance(questions, list) or len(questions) == 0:
            return {"success": False, "error": "Quiz must include at least one question."}

        for qid in questions:
            q = self.questions.get(qid)
            if not q or not q.get("active", False):
                return {
                    "success": False,
                    "error": f"Question ID '{qid}' does not exist or is not active."
                }

        self.quizzes[quiz_id] = {
            "quiz_id": quiz_id,
            "quiz_title": quiz_title,
            "description": description,
            "subject": subject,
            "difficulty": difficulty,
            "questions": questions[:],  # shallow copy
        }

        return {"success": True, "message": f"Quiz '{quiz_id}' created successfully."}

    def add_question_to_quiz(self, quiz_id: str, question_id: str) -> dict:
        """
        Add an existing active question to a quiz.

        Args:
            quiz_id (str): The quiz to add the question to.
            question_id (str): The question to add.

        Returns:
            dict: {
                "success": True,
                "message": "Question <question_id> added to quiz <quiz_id>"
            }
            or {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Only active questions may be added to quizzes.
            - A quiz and question with the given ids must exist.
            - Do not add duplicate questions to the same quiz.
        """
        quiz = self.quizzes.get(quiz_id)
        if not quiz:
            return { "success": False, "error": f"Quiz '{quiz_id}' does not exist" }

        question = self.questions.get(question_id)
        if not question:
            return { "success": False, "error": f"Question '{question_id}' does not exist" }

        if not question.get("active", False):
            return { "success": False, "error": f"Question '{question_id}' is not active" }

        if question_id in quiz.get("questions", []):
            return { "success": False, "error": f"Question '{question_id}' is already in quiz '{quiz_id}'" }

        quiz["questions"].append(question_id)
        return { "success": True, "message": f"Question '{question_id}' added to quiz '{quiz_id}'" }

    def record_quiz_attempt(
        self,
        user_id: str,
        quiz_id: str,
        timestamp: str,
        score: float,
        responses: list
    ) -> dict:
        """
        Save a new user attempt for a quiz with responses and score.

        Args:
            user_id (str): ID of the user attempting the quiz (must exist).
            quiz_id (str): ID of the quiz being attempted (must exist).
            timestamp (str): Timestamp of the attempt.
            score (float): Score achieved in the attempt.
            responses (list): List of {"question_id": ..., "answer_id": ...}
                              Each question_id must be in the quiz.

        Returns:
            dict: {
                "success": True,
                "message": "Quiz attempt recorded",
                "attempt_id": str
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - user_id must exist
            - quiz_id must exist
            - responses must be non-empty and question_ids must be in quiz's questions
        """
        # Validate user and quiz
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
        if quiz_id not in self.quizzes:
            return { "success": False, "error": "Quiz does not exist" }
        if not isinstance(responses, list) or len(responses) == 0:
            return { "success": False, "error": "Responses must be a non-empty list" }

        quiz_question_ids = set(self.quizzes[quiz_id]["questions"])
        for resp in responses:
            if (
                not isinstance(resp, dict)
                or "question_id" not in resp
                or "answer_id" not in resp
                or resp["question_id"] not in quiz_question_ids
            ):
                return {
                    "success": False,
                    "error": "Invalid response entry or question not in quiz"
                }

        # Generate unique attempt_id
        i = 1
        while True:
            attempt_id = f"attempt_{len(self.attempts) + i}"
            if attempt_id not in self.attempts:
                break
            i += 1

        attempt_info = {
            "attempt_id": attempt_id,
            "user_id": user_id,
            "quiz_id": quiz_id,
            "timestamp": timestamp,
            "score": float(score),
            "responses": responses,
        }

        self.attempts[attempt_id] = attempt_info

        return {
            "success": True,
            "message": "Quiz attempt recorded",
            "attempt_id": attempt_id
        }

    def update_quiz_attempt_score(self, attempt_id: str, new_score: float) -> dict:
        """
        Update the score of a user's quiz attempt.

        Args:
            attempt_id (str): The unique identifier of the attempt to update.
            new_score (float): The new score to assign to this attempt. Must be non-negative.

        Returns:
            dict: Success or error message:
                - { "success": True, "message": "Score updated successfully." }
                - { "success": False, "error": <reason> }

        Constraints:
            - Attempt with attempt_id must exist.
            - new_score must be non-negative.
        """
        if attempt_id not in self.attempts:
            return { "success": False, "error": "Attempt does not exist." }
        if not isinstance(new_score, (int, float)) or new_score < 0:
            return { "success": False, "error": "Invalid score value." }
        self.attempts[attempt_id]["score"] = float(new_score)
        return { "success": True, "message": "Score updated successfully." }


class OnlineQuizManagementSystem(BaseEnv):
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

    def get_questions_by_subject_and_difficulty(self, **kwargs):
        return self._call_inner_tool('get_questions_by_subject_and_difficulty', kwargs)

    def get_active_question_by_id(self, **kwargs):
        return self._call_inner_tool('get_active_question_by_id', kwargs)

    def get_answers_by_question_id(self, **kwargs):
        return self._call_inner_tool('get_answers_by_question_id', kwargs)

    def get_correct_answers_by_question_id(self, **kwargs):
        return self._call_inner_tool('get_correct_answers_by_question_id', kwargs)

    def list_quizzes(self, **kwargs):
        return self._call_inner_tool('list_quizzes', kwargs)

    def get_quiz_by_id(self, **kwargs):
        return self._call_inner_tool('get_quiz_by_id', kwargs)

    def get_questions_in_quiz(self, **kwargs):
        return self._call_inner_tool('get_questions_in_quiz', kwargs)

    def get_attempts_by_user_id(self, **kwargs):
        return self._call_inner_tool('get_attempts_by_user_id', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def get_attempt_detail(self, **kwargs):
        return self._call_inner_tool('get_attempt_detail', kwargs)

    def activate_question(self, **kwargs):
        return self._call_inner_tool('activate_question', kwargs)

    def deactivate_question(self, **kwargs):
        return self._call_inner_tool('deactivate_question', kwargs)

    def activate_answer(self, **kwargs):
        return self._call_inner_tool('activate_answer', kwargs)

    def deactivate_answer(self, **kwargs):
        return self._call_inner_tool('deactivate_answer', kwargs)

    def add_question(self, **kwargs):
        return self._call_inner_tool('add_question', kwargs)

    def add_answer(self, **kwargs):
        return self._call_inner_tool('add_answer', kwargs)

    def update_question_content(self, **kwargs):
        return self._call_inner_tool('update_question_content', kwargs)

    def update_answer_text(self, **kwargs):
        return self._call_inner_tool('update_answer_text', kwargs)

    def create_quiz(self, **kwargs):
        return self._call_inner_tool('create_quiz', kwargs)

    def add_question_to_quiz(self, **kwargs):
        return self._call_inner_tool('add_question_to_quiz', kwargs)

    def record_quiz_attempt(self, **kwargs):
        return self._call_inner_tool('record_quiz_attempt', kwargs)

    def update_quiz_attempt_score(self, **kwargs):
        return self._call_inner_tool('update_quiz_attempt_score', kwargs)

