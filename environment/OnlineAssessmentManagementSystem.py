# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import time
from datetime import datetime



class UserInfo(TypedDict):
    _id: str
    name: str
    email: str
    user_rol: str

class TestInfo(TypedDict):
    _id: str
    title: str
    description: str
    creator_id: str
    total_points: float
    sta: str  # status

class TestAttemptInfo(TypedDict):
    attempt_id: str
    user_id: str
    test_id: str
    start_time: str  # or float, depending on implementation
    end_time: str    # or float
    score: float
    sta: str  # status

class TestResponseInfo(TypedDict):
    attempt_id: str
    question_id: str
    response_content: str
    is_correct: bool
    points_awarded: float

class QuestionInfo(TypedDict):
    question_id: str
    test_id: str
    question_text: str
    correct_answer: str
    max_poin: float  # max_points

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for managing users, tests, attempts, questions, and responses
        in an online assessment system.
        """

        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Tests: {_id: TestInfo}
        self.tests: Dict[str, TestInfo] = {}

        # TestAttempts: {attempt_id: TestAttemptInfo}
        self.test_attempts: Dict[str, TestAttemptInfo] = {}

        # TestResponses: {attempt_id: List[TestResponseInfo]}
        self.test_responses: Dict[str, List[TestResponseInfo]] = {}

        # Questions: {question_id: QuestionInfo}
        self.questions: Dict[str, QuestionInfo] = {}

        # Constraints:
        # - Each TestAttempt must be associated with one user and one test.
        # - Users can have multiple attempts per test, unless limited by policy.
        # - Each TestResponse must be linked to a TestAttempt and a Question.
        # - Scores are computed based on responses and stored with each TestAttempt.
        # - Only authorized users (test owners, administrators, or the test-taking user) can view specific results.

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user information using the user's unique identifier.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict:
                - If found: {"success": True, "data": UserInfo}
                - If not found: {"success": False, "error": "User not found"}
        Constraints:
            - The given user_id must correspond to an existing user in the system.
        """
        user = self.users.get(user_id)
        if user is None:
            return {"success": False, "error": "User not found"}
        return {"success": True, "data": user}

    def get_user_by_name(self, name: str) -> dict:
        """
        Retrieve user information(s) using the user's name.

        Args:
            name (str): The user's name to search for.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": List[UserInfo],  # One or more users with that name
                    }
                - On failure (no such user):
                    {
                        "success": False,
                        "error": "No user found with the given name"
                    }

        Constraints:
            - User name matching is case-sensitive.
            - Returns all users with the given name (names may not be unique).
        """
        if not name:
            return { "success": False, "error": "No user name provided" }
    
        matched_users = [user for user in self.users.values() if user['name'] == name]
        if not matched_users:
            return { "success": False, "error": "No user found with the given name" }

        return { "success": True, "data": matched_users }

    def get_user_role(self, user_id: str) -> dict:
        """
        Retrieve the user's role (candidate, admin, etc.) given their user ID.

        Args:
            user_id (str): The ID of the user whose role is requested.

        Returns:
            dict: 
                On success: { "success": True, "data": <role_str> }
                On failure: { "success": False, "error": "User not found" }

        Constraints:
            - The given user_id must exist in the system.
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }

        return { "success": True, "data": user["user_rol"] }

    def get_test_by_id(self, test_id: str) -> dict:
        """
        Retrieve the test's information by test ID.

        Args:
            test_id (str): The unique identifier of the test.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": TestInfo  # All test info fields (title, description, creator_id, total_points, sta, _id)
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Test not found"
                    }

        Constraints:
            - test_id must exist in the system.
        """
        test_info = self.tests.get(test_id)
        if test_info is None:
            return { "success": False, "error": "Test not found" }
        return { "success": True, "data": test_info }

    def get_tests_by_creator(self, creator_id: str) -> dict:
        """
        Retrieve all tests created by a specific user.

        Args:
            creator_id (str): The user ID of the test creator.

        Returns:
            dict: {
                "success": True,
                "data": List[TestInfo],  # List of test info created by the user, may be empty if none
            }
            or
            {
                "success": False,
                "error": str  # If user does not exist
            }
        Constraints:
            - The specified creator user must exist in the system.
        """
        if creator_id not in self.users:
            return { "success": False, "error": "User not found" }

        tests_created = [
            test_info for test_info in self.tests.values()
            if test_info["creator_id"] == creator_id
        ]
        return { "success": True, "data": tests_created }

    def get_test_attempts_by_user_and_test(
        self,
        user_id: str,
        test_id: str,
        status: str = None,
        sort_by: str = None,
        descending: bool = False
    ) -> dict:
        """
        List all of a user's attempts for a particular test, with optional status filter and sorting.

        Args:
            user_id (str): The user's ID whose attempts are to be listed.
            test_id (str): The test's ID to filter attempts for.
            status (str, optional): Status value to filter attempts (e.g., 'completed').
            sort_by (str, optional): Field name by which to sort ('start_time' or 'end_time').
            descending (bool, optional): Sort descendingly if True (default False).

        Returns:
            dict: {
                "success": True,
                "data": List[TestAttemptInfo],  # May be empty
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - If user or test does not exist, return an empty list.
            - If status given, only attempts with given status are included.
            - If sort_by is invalid, returns error.
        """
        # Optional: Check user and test existence (return empty list if missing)
        if user_id not in self.users or test_id not in self.tests:
            return {"success": True, "data": []}

        # Get attempts for this user/test
        attempts = [
            attempt for attempt in self.test_attempts.values()
            if attempt["user_id"] == user_id and attempt["test_id"] == test_id
        ]

        # Filter by status if needed
        if status is not None:
            attempts = [a for a in attempts if a.get("sta") == status]

        # Sorting if requested
        if sort_by is not None:
            if sort_by not in ("start_time", "end_time"):
                return {"success": False, "error": f"Invalid sort_by field: {sort_by}"}
            # Sorting values may be None or invalid: use stable sorting
            attempts.sort(
                key=lambda a: (a[sort_by] is None, a[sort_by]),  # Nones last
                reverse=descending
            )

        return {"success": True, "data": attempts}

    def get_most_recent_attempt_by_user_and_test(self, user_id: str, test_id: str) -> dict:
        """
        Retrieve the most recent TestAttempt for the given user and test.

        Args:
            user_id (str): The user's unique ID.
            test_id (str): The test's unique ID.

        Returns:
            dict: {
                "success": True,
                "data": TestAttemptInfo | None  # The most recent attempt info or None if not found
            }

        Constraints:
            - Finds the attempt with largest start_time (most recent) for the user/test pair.
            - Returns None if no such attempt exists.
        """
        attempts = [
            attempt for attempt in self.test_attempts.values()
            if attempt["user_id"] == user_id and attempt["test_id"] == test_id
        ]

        if not attempts:
            return {"success": True, "data": None}

        # Parse start_time; assume it's float, but try to convert if string
        def parse_time(val):
            try:
                return float(val)
            except Exception:
                try:
                    return datetime.fromisoformat(str(val).replace("Z", "+00:00")).timestamp()
                except Exception:
                    return 0.0

        most_recent = max(
            attempts,
            key=lambda att: parse_time(att.get("start_time", 0))
        )

        return {"success": True, "data": most_recent}

    def get_test_attempt_by_id(self, attempt_id: str) -> dict:
        """
        Retrieve detailed info (start_time, end_time, score, status) for a given test attempt.

        Args:
            attempt_id (str): The unique ID of the test attempt to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": TestAttemptInfo
            }
            or
            {
                "success": False,
                "error": str  # "Test attempt does not exist"
            }

        Constraints:
            - The specified attempt_id must exist in the system.
        """
        attempt = self.test_attempts.get(attempt_id)
        if not attempt:
            return { "success": False, "error": "Test attempt does not exist" }
        return { "success": True, "data": attempt }

    def get_test_responses_by_attempt_id(self, attempt_id: str) -> dict:
        """
        Retrieve all responses (TestResponseInfo) for a given test attempt identifier.

        Args:
            attempt_id (str): The ID of the test attempt.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": List[TestResponseInfo]  # May be empty if no responses.
                    }
                - On failure (invalid attempt_id):
                    {
                        "success": False,
                        "error": "Test attempt not found"
                    }
        Constraints:
            - The attempt_id must exist in self.test_attempts.
            - No authorization is checked in this method (should be checked separately if required).
        """
        if attempt_id not in self.test_attempts:
            return { "success": False, "error": "Test attempt not found" }
    
        responses = self.test_responses.get(attempt_id, [])
        return { "success": True, "data": responses }

    def get_question_by_id(self, question_id: str) -> dict:
        """
        Retrieve full details for the specified question, including correct answer and maximum points.

        Args:
            question_id (str): The unique ID of the question to retrieve.

        Returns:
            dict:
                {
                    "success": True,
                    "data": QuestionInfo
                }
                or
                {
                    "success": False,
                    "error": "Question not found"
                }

        Constraints:
            - question_id must exist in the questions database.
        """
        question = self.questions.get(question_id)
        if question is None:
            return { "success": False, "error": "Question not found" }
        return { "success": True, "data": question }

    def get_questions_for_test(self, test_id: str) -> dict:
        """
        Retrieve all questions (with metadata) that belong to the specified test.

        Args:
            test_id (str): ID of the test whose questions are requested.

        Returns:
            dict: 
                - On success: {
                    "success": True,
                    "data": List[QuestionInfo],  # All questions for the test (empty list if none)
                }
                - On failure: {
                    "success": False,
                    "error": str  # Reason for failure, e.g. test not found
                }

        Constraints:
            - The specified test_id must exist in the system.
        """
        if test_id not in self.tests:
            return {
                "success": False,
                "error": "Test not found"
            }

        questions = [
            question for question in self.questions.values()
            if question.get("test_id") == test_id
        ]
        return {
            "success": True,
            "data": questions
        }

    def check_user_authorized_for_attempt_result(self, user_id: str, attempt_id: str) -> dict:
        """
        Determine if a user is authorized to view the result for a given test attempt.

        Args:
            user_id (str): The ID of the user requesting access.
            attempt_id (str): The ID of the test attempt in question.

        Returns:
            dict: {
                "success": True,
                "authorized": bool  # True if authorized, False otherwise
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - Only authorized users (test owners, administrators, or the test-taking user) can view specific results.
            - All entities must exist.
        """
        # Check that the user exists
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User does not exist" }

        # Check that the attempt exists
        attempt = self.test_attempts.get(attempt_id)
        if not attempt:
            return { "success": False, "error": "Test attempt does not exist" }

        # Check that the relevant test exists
        test = self.tests.get(attempt["test_id"])
        if not test:
            return { "success": False, "error": "Test does not exist for this attempt" }

        # Admins always have access
        if user.get("user_rol", "").lower() == "admin":
            return { "success": True, "authorized": True }
    
        # Test-taker can view their own result
        if attempt["user_id"] == user_id:
            return { "success": True, "authorized": True }

        # Test creator can view any user's results for their test
        if test["creator_id"] == user_id:
            return { "success": True, "authorized": True }

        # Otherwise, not authorized
        return { "success": True, "authorized": False }

    def get_attempt_score(self, attempt_id: str) -> dict:
        """
        Retrieve the final score for a given test attempt.

        Args:
            attempt_id (str): The unique identifier for the test attempt.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": float  # The score for the specified test attempt
                    }
                - On failure:
                    {
                        "success": False,
                        "error": str  # Description of the error (e.g., test attempt not found)
                    }

        Constraints:
            - The test attempt with the given attempt_id must exist.
        """
        attempt = self.test_attempts.get(attempt_id)
        if not attempt:
            return { "success": False, "error": "Test attempt not found" }
        # Score should always be present, but check defensively
        score = attempt.get("score")
        if score is None:
            return { "success": False, "error": "Score not available for this attempt" }
        return { "success": True, "data": score }


    def create_test_attempt(
        self,
        attempt_id: str,
        user_id: str,
        test_id: str,
        start_time: str = None  # Optional, default to current time if not specified
    ) -> dict:
        """
        Create a new test attempt record for a user and a test.

        Args:
            attempt_id (str): Unique identifier for the new test attempt.
            user_id (str): The user's ID who is attempting the test.
            test_id (str): The test's ID being attempted.
            start_time (str, optional): Timestamp when the attempt starts. Defaults to current time.

        Returns:
            dict: {
                "success": True,
                "message": "Test attempt created",
                "attempt_id": str
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - attempt_id must be unique.
            - user_id and test_id must exist.
        """
        if attempt_id in self.test_attempts:
            return {"success": False, "error": "Attempt ID already exists"}

        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        if test_id not in self.tests:
            return {"success": False, "error": "Test does not exist"}

        now_time = start_time or str(time.time())
        # Initial values (end_time: None, score: 0.0, status: 'in_progress')
        new_attempt = {
            "attempt_id": attempt_id,
            "user_id": user_id,
            "test_id": test_id,
            "start_time": now_time,
            "end_time": None,
            "score": 0.0,
            "sta": 'in_progress'
        }

        self.test_attempts[attempt_id] = new_attempt

        return {
            "success": True,
            "message": "Test attempt created",
            "attempt_id": attempt_id
        }

    def update_test_attempt_score(self, attempt_id: str) -> dict:
        """
        Update or calculate the score for a test attempt based on its responses.
    
        Args:
            attempt_id (str): Unique identifier for the test attempt to update/rescore.

        Returns:
            dict:
                On success: {
                    "success": True,
                    "message": "Updated score for attempt <attempt_id> to <score_value>"
                }
                On failure: {
                    "success": False,
                    "error": <error string>
                }

        Constraints:
            - The attempt must exist in the system.
            - The score is calculated as the sum of 'points_awarded' from all responses for the attempt.
            - If no responses exist, score is set to 0.
        """
        if attempt_id not in self.test_attempts:
            return {"success": False, "error": "TestAttempt not found"}

        # Retrieve all responses for this attempt, if any
        responses = self.test_responses.get(attempt_id, [])
        score = sum(response.get('points_awarded', 0) for response in responses)
    
        # Update the attempt's score
        self.test_attempts[attempt_id]['score'] = score

        return {
            "success": True,
            "message": f"Updated score for attempt {attempt_id} to {score}"
        }

    def submit_test_response(
        self,
        attempt_id: str,
        question_id: str,
        response_content: str
    ) -> dict:
        """
        Store or update an individual response for a question in a test attempt.

        Args:
            attempt_id (str): ID of the test attempt.
            question_id (str): ID of the question being answered.
            response_content (str): User's answer for the question.

        Returns:
            dict: {
                "success": True,
                "message": "Created/Updated response for ...",
            } or {
                "success": False,
                "error": str
            }

        Constraints:
            - attempt_id must exist in self.test_attempts.
            - question_id must exist in self.questions.
            - Question's test_id must match attempt's test_id.
            - Updates existing response if already present for this question in this attempt.
            - is_correct is computed via string comparison on response_content (case-insensitive, stripped).
            - points_awarded equals max_poin if correct, else 0.
        """
        # Validate attempt
        attempt = self.test_attempts.get(attempt_id)
        if not attempt:
            return {"success": False, "error": "Test attempt does not exist."}

        # Validate question
        question = self.questions.get(question_id)
        if not question:
            return {"success": False, "error": "Question does not exist."}

        # Test-Question association
        if question["test_id"] != attempt["test_id"]:
            return {"success": False, "error": "Question does not belong to the test of this attempt."}

        # Compute correctness/points (simple exact string match, case-insensitive, stripped)
        correct_answer = question.get("correct_answer", "")
        user_response = response_content.strip() if response_content else ""
        is_correct = (user_response.lower() == correct_answer.strip().lower())
        points_awarded = float(question.get("max_poin", 0)) if is_correct else 0.0

        # Need to check if this attempt already has a response for this question
        response_list = self.test_responses.setdefault(attempt_id, [])
        updated = False
        for resp in response_list:
            if resp["question_id"] == question_id:
                # Update
                resp["response_content"] = response_content
                resp["is_correct"] = is_correct
                resp["points_awarded"] = points_awarded
                updated = True
                break

        if not updated:
            # Add new
            new_resp = {
                "attempt_id": attempt_id,
                "question_id": question_id,
                "response_content": response_content,
                "is_correct": is_correct,
                "points_awarded": points_awarded,
            }
            response_list.append(new_resp)
            return {
                "success": True,
                "message": f"Created response for question {question_id} in attempt {attempt_id}."
            }
        else:
            return {
                "success": True,
                "message": f"Updated response for question {question_id} in attempt {attempt_id}."
            }

    def recalculate_attempt_score_from_responses(self, attempt_id: str) -> dict:
        """
        Recompute and update the score for a TestAttempt based on its responses.
    
        Args:
            attempt_id (str): The ID of the attempt to update.
        
        Returns:
            dict: 
                On success:
                {
                    "success": True,
                    "message": "Score recalculated",
                    "new_score": float
                }
                On failure:
                {
                    "success": False,
                    "error": str
                }
        Constraints:
            - The attempt_id must exist in self.test_attempts.
            - The score is set as the sum of points_awarded for all responses under this attempt.
            - If there are no responses, score is 0.0.
        """
        if attempt_id not in self.test_attempts:
            return { "success": False, "error": "Attempt ID does not exist." }

        responses = self.test_responses.get(attempt_id, [])
        new_score = sum(
            response.get("points_awarded", 0.0)
            for response in responses
        )
        self.test_attempts[attempt_id]["score"] = new_score
    
        return {
            "success": True,
            "message": "Score recalculated",
            "new_score": new_score
        }

    def set_test_attempt_status(self, attempt_id: str, new_status: str) -> dict:
        """
        Update the status ('sta') of a TestAttempt.

        Args:
            attempt_id (str): ID of the TestAttempt to update.
            new_status (str): The status value to set (e.g., "completed", "in progress").

        Returns:
            dict: 
                { "success": True, "message": "Test attempt status updated." }
                or
                { "success": False, "error": "reason" }

        Constraints:
            - The attempt_id must exist in the system.
        """
        if attempt_id not in self.test_attempts:
            return {"success": False, "error": "TestAttempt not found."}
    
        self.test_attempts[attempt_id]['sta'] = new_status
        return {"success": True, "message": "Test attempt status updated."}


class OnlineAssessmentManagementSystem(BaseEnv):
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

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def get_user_by_name(self, **kwargs):
        return self._call_inner_tool('get_user_by_name', kwargs)

    def get_user_role(self, **kwargs):
        return self._call_inner_tool('get_user_role', kwargs)

    def get_test_by_id(self, **kwargs):
        return self._call_inner_tool('get_test_by_id', kwargs)

    def get_tests_by_creator(self, **kwargs):
        return self._call_inner_tool('get_tests_by_creator', kwargs)

    def get_test_attempts_by_user_and_test(self, **kwargs):
        return self._call_inner_tool('get_test_attempts_by_user_and_test', kwargs)

    def get_most_recent_attempt_by_user_and_test(self, **kwargs):
        return self._call_inner_tool('get_most_recent_attempt_by_user_and_test', kwargs)

    def get_test_attempt_by_id(self, **kwargs):
        return self._call_inner_tool('get_test_attempt_by_id', kwargs)

    def get_test_responses_by_attempt_id(self, **kwargs):
        return self._call_inner_tool('get_test_responses_by_attempt_id', kwargs)

    def get_question_by_id(self, **kwargs):
        return self._call_inner_tool('get_question_by_id', kwargs)

    def get_questions_for_test(self, **kwargs):
        return self._call_inner_tool('get_questions_for_test', kwargs)

    def check_user_authorized_for_attempt_result(self, **kwargs):
        return self._call_inner_tool('check_user_authorized_for_attempt_result', kwargs)

    def get_attempt_score(self, **kwargs):
        return self._call_inner_tool('get_attempt_score', kwargs)

    def create_test_attempt(self, **kwargs):
        return self._call_inner_tool('create_test_attempt', kwargs)

    def update_test_attempt_score(self, **kwargs):
        return self._call_inner_tool('update_test_attempt_score', kwargs)

    def submit_test_response(self, **kwargs):
        return self._call_inner_tool('submit_test_response', kwargs)

    def recalculate_attempt_score_from_responses(self, **kwargs):
        return self._call_inner_tool('recalculate_attempt_score_from_responses', kwargs)

    def set_test_attempt_status(self, **kwargs):
        return self._call_inner_tool('set_test_attempt_status', kwargs)
