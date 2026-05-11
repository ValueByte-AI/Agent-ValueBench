# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



# Entity: Question
class QuestionInfo(TypedDict):
    question_id: str
    title: str
    body: str
    author_user_id: str
    created_at: str
    updated_at: str
    tags: List[str]  # List of tag_ids
    view_count: int
    sta: str  # Left as is due to source typo/ambiguity

# Entity: Answer
class AnswerInfo(TypedDict):
    answer_id: str
    question_id: str
    body: str
    author_user_id: str
    created_at: str
    updated_at: str
    score: int
    is_accepted: bool

# Entity: User
class UserInfo(TypedDict):
    _id: str
    username: str
    reputation: int
    registration_date: str
    profile_info: str

# Entity: Tag
class TagInfo(TypedDict):
    ag_id: str   # Left as is due to source typo
    tag_name: str
    tag_description: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Questions: {question_id: QuestionInfo}
        self.questions: Dict[str, QuestionInfo] = {}

        # Answers: {answer_id: AnswerInfo}
        self.answers: Dict[str, AnswerInfo] = {}

        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Tags: {ag_id: TagInfo}
        self.tags: Dict[str, TagInfo] = {}

        # Constraints:
        # - Each answer must reference a valid question via question_id.
        # - Sorting answers by created_at timestamps enables retrieval as per time-based criteria.
        # - Only registered users can post questions and answers.
        # - A question can have multiple tags and answers.
        # - Deletion, editing, and voting actions (not shown in this task) can affect questions and answers.

    def get_question_by_id(self, question_id: str) -> dict:
        """
        Retrieve the full information of a question specified by its question_id.
    
        Args:
            question_id (str): Unique ID of the question to fetch.

        Returns:
            dict:
                success: True, data: QuestionInfo (if found)
                success: False, error: str (if not found)
        Constraints:
            - question_id must exist in the system.
        """
        question = self.questions.get(question_id)
        if question is None:
            return {"success": False, "error": "Question not found"}
        return {"success": True, "data": question}

    def get_answers_for_question(self, question_id: str) -> dict:
        """
        Retrieve all answer records associated with a specified question.

        Args:
            question_id (str): The unique identifier of the question whose answers should be retrieved.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[AnswerInfo]  # may be empty if no answers for this question
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # reason for failure, e.g. "Question does not exist"
                    }
        Constraints:
            - The question_id must exist in the platform (question must be present).
            - All answers returned have their question_id equal to the given question_id.
        """
        if question_id not in self.questions:
            return {"success": False, "error": "Question does not exist"}

        answer_list = [
            answer for answer in self.answers.values()
            if answer["question_id"] == question_id
        ]

        return {"success": True, "data": answer_list}

    def get_answers_for_question_sorted(
        self, 
        question_id: str, 
        sort_by: str = "created_at", 
        descending: bool = True
    ) -> dict:
        """
        Fetch all answers for a given question, sorted by a specified attribute.

        Args:
            question_id (str): The ID of the question to fetch answers for.
            sort_by (str, optional): Attribute to sort answers by (must be an AnswerInfo key, default 'created_at').
            descending (bool, optional): If True, sort descending (most recent/biggest first). Default is True.

        Returns:
            dict: {
                "success": True,
                "data": List[AnswerInfo],  # Sorted list of answers (empty if none)
            }
            Or
            {
                "success": False,
                "error": str  # Error message
            }

        Constraints:
            - question_id must refer to an existing question.
            - sort_by attribute must be a valid key of AnswerInfo.
        """
        if question_id not in self.questions:
            return { "success": False, "error": "Question does not exist" }

        # Find all answers linked to this question
        answers = [
            answer for answer in self.answers.values()
            if answer["question_id"] == question_id
        ]

        if not answers:
            return { "success": True, "data": [] }

        # Validate sort_by attribute
        if len(answers) > 0 and sort_by not in answers[0]:
            return { 
                "success": False, 
                "error": f"Invalid sort_by attribute: {sort_by}"
            }

        sorted_answers = sorted(
            answers, 
            key=lambda a: a[sort_by], 
            reverse=descending
        )

        return { "success": True, "data": sorted_answers }

    def get_user_by_id(self, _id: str) -> dict:
        """
        Retrieve user profile information by the user's unique _id.

        Args:
            _id (str): The unique user ID.

        Returns:
            dict:
                On success: { "success": True, "data": UserInfo }
                On failure: { "success": False, "error": "User not found" }

        Constraints:
            - The _id must correspond to a registered user.
        """
        user = self.users.get(_id)
        if user is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user }

    def get_tag_by_id(self, ag_id: str) -> dict:
        """
        Retrieve the metadata for a tag given its unique ag_id.

        Args:
            ag_id (str): The unique identifier for the tag.

        Returns:
            dict: 
                - If found: { "success": True, "data": TagInfo }
                - If not found: { "success": False, "error": "Tag not found" }

        Constraints:
            - ag_id must correspond to an existing tag in the platform.
        """
        tag = self.tags.get(ag_id)
        if tag is None:
            return { "success": False, "error": "Tag not found" }
        return { "success": True, "data": tag }

    def list_tags_for_question(self, question_id: str) -> dict:
        """
        Retrieve all tags (tag info dicts) associated with a specified question.

        Args:
            question_id (str): The unique identifier of the question.

        Returns:
            dict: {
                "success": True,
                "data": List[TagInfo],  # list of tag info dictionaries, may be empty if no tags
            }
            or
            {
                "success": False,
                "error": str  # error message, e.g., question not found
            }

        Constraints:
            - The question_id must exist in the questions collection.
            - Tags that do not exist in the system are skipped.
        """
        question = self.questions.get(question_id)
        if question is None:
            return {"success": False, "error": "Question not found"}

        tag_ids = question.get("tags", [])
        tag_infos = []
        for tag_id in tag_ids:
            tag_info = self.tags.get(tag_id)
            if tag_info:
                tag_infos.append(tag_info)

        return {"success": True, "data": tag_infos}

    def list_questions_by_tag(self, tag_id: str) -> dict:
        """
        Retrieve all questions associated with a specific tag.

        Args:
            tag_id (str): The unique tag identifier (ag_id).

        Returns:
            dict: {
                "success": True,
                "data": List[QuestionInfo],  # List of all questions tagged with tag_id,
            }
            or
            {
                "success": False,
                "error": str,  # Error reason, e.g. tag does not exist
            }

        Constraints:
            - The tag must exist in the system (ag_id in self.tags).
            - It's valid to return an empty list if no questions use the tag.
        """
        if tag_id not in self.tags:
            return { "success": False, "error": "Tag does not exist" }

        matched_questions = [
            question
            for question in self.questions.values()
            if tag_id in question["tags"]
        ]

        return { "success": True, "data": matched_questions }

    def get_question_list_by_user(self, user_id: str) -> dict:
        """
        List all questions posted by a particular user.

        Args:
            user_id (str): The unique user _id for the user whose questions are requested.

        Returns:
            dict: {
                "success": True,
                "data": List[QuestionInfo],  # List of questions authored by the given user (can be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g. "User does not exist"
            }

        Constraints:
            - user_id must correspond to a registered user (exists in self.users).
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        questions_by_user = [
            qinfo for qinfo in self.questions.values()
            if qinfo["author_user_id"] == user_id
        ]
        return {"success": True, "data": questions_by_user}

    def get_answer_list_by_user(self, user_id: str) -> dict:
        """
        Lists all answers posted by a particular user.

        Args:
            user_id (str): The user ID whose answers are to be retrieved.

        Returns:
            dict: {
                "success": True,
                "data": List[AnswerInfo],   # List may be empty if user has posted no answers.
            }
            or
            {
                "success": False,
                "error": str  # Error message if user does not exist.
            }

        Constraints:
            - The user must exist in the system (registered user).
            - Returned answers are all authored by the specified user.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }

        answers_by_user = [
            answer for answer in self.answers.values()
            if answer["author_user_id"] == user_id
        ]

        return { "success": True, "data": answers_by_user }

    def none_required_for_the_example_task(self, *args, **kwargs) -> dict:
        """
        No state change operation is required or implemented for this use case.
        This placeholder exists to satisfy API stubs or erroneous calls.
        Args:
            *args, **kwargs: Ignored.

        Returns:
            dict: {
                "success": False,
                "error": "No state-changing operation required or implemented for this example task."
            }
        """
        return {
            "success": False,
            "error": "No state-changing operation required or implemented for this example task."
        }


class OnlineQandAPlatform(BaseEnv):
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

    def get_question_by_id(self, **kwargs):
        return self._call_inner_tool('get_question_by_id', kwargs)

    def get_answers_for_question(self, **kwargs):
        return self._call_inner_tool('get_answers_for_question', kwargs)

    def get_answers_for_question_sorted(self, **kwargs):
        return self._call_inner_tool('get_answers_for_question_sorted', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def get_tag_by_id(self, **kwargs):
        return self._call_inner_tool('get_tag_by_id', kwargs)

    def list_tags_for_question(self, **kwargs):
        return self._call_inner_tool('list_tags_for_question', kwargs)

    def list_questions_by_tag(self, **kwargs):
        return self._call_inner_tool('list_questions_by_tag', kwargs)

    def get_question_list_by_user(self, **kwargs):
        return self._call_inner_tool('get_question_list_by_user', kwargs)

    def get_answer_list_by_user(self, **kwargs):
        return self._call_inner_tool('get_answer_list_by_user', kwargs)

    def none_required_for_the_example_task(self, **kwargs):
        return self._call_inner_tool('none_required_for_the_example_task', kwargs)

