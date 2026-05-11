# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, Optional, Tuple, TypedDict, Any
import uuid
from datetime import datetime



class SurveyInfo(TypedDict):
    survey_id: str
    title: str
    description: str
    creator_id: str
    created_at: str
    status: str  # e.g., 'draft', 'published', 'closed'

class QuestionInfo(TypedDict):
    question_id: str
    survey_id: str
    text: str
    type: str  # e.g., 'single-choice', 'multiple-choice', etc.
    order: int

class OptionInfo(TypedDict):
    option_id: str
    question_id: str
    text: str
    order: int

class ParticipantInfo(TypedDict, total=False):
    participant_id: str
    user_id: Optional[str] # May be None for anonymous participants
    demographic_info: Optional[Dict[str, Any]]  # Optional demographic info

class ResponseInfo(TypedDict):
    response_id: str
    participant_id: str
    survey_id: str
    question_id: str
    selected_option_id: str
    answered_at: str

class AggregatedResultInfo(TypedDict):
    survey_id: str
    question_id: str
    option_id: str
    response_count: int

class _GeneratedEnvImpl:
    def __init__(self):
        # Surveys: {survey_id: SurveyInfo}
        self.surveys: Dict[str, SurveyInfo] = {}
        # Questions: {question_id: QuestionInfo}
        self.questions: Dict[str, QuestionInfo] = {}
        # Options: {option_id: OptionInfo}
        self.options: Dict[str, OptionInfo] = {}
        # Participants: {participant_id: ParticipantInfo}
        self.participants: Dict[str, ParticipantInfo] = {}
        # Responses: {response_id: ResponseInfo}
        self.responses: Dict[str, ResponseInfo] = {}
        # AggregatedResults: {(survey_id, question_id, option_id): AggregatedResultInfo}
        self.aggregated_results: Dict[Tuple[str, str, str], AggregatedResultInfo] = {}

        # Constraints:
        # - Each question must belong to one and only one survey.
        # - Each option must belong to exactly one question.
        # - A participant can respond only once per question per survey (unless survey allows multiple attempts).
        # - Option selections in responses must reference existing options for the corresponding question.
        # - Surveys can only be answered if their status is "published".
        # - Question and option order must be preserved as specified.

    def get_survey_by_id(self, survey_id: str) -> dict:
        """
        Retrieve all information (metadata) about a specific survey by its survey_id.

        Args:
            survey_id (str): The unique identifier of the survey.

        Returns:
            dict: {
                "success": True,
                "data": SurveyInfo  # The full metadata dict for the survey
            }
            or
            {
                "success": False,
                "error": "Survey not found"
            }

        Constraints:
            - The survey_id must exist in the surveys dictionary.
        """
        survey = self.surveys.get(survey_id)
        if survey is None:
            return { "success": False, "error": "Survey not found" }
        return { "success": True, "data": survey }

    def list_surveys(self) -> dict:
        """
        List all surveys with their metadata.

        Returns:
            dict: {
                "success": True,
                "data": List[SurveyInfo]  # May be empty if no surveys exist
            }
        """
        surveys = list(self.surveys.values())
        return {"success": True, "data": surveys}

    def get_questions_by_survey(self, survey_id: str) -> dict:
        """
        Get all questions belonging to the specified survey, sorted by their `order` attribute.

        Args:
            survey_id (str): The ID of the survey whose questions are to be retrieved.

        Returns:
            dict: 
                - On success: {
                    "success": True,
                    "data": List[QuestionInfo]  # In order (may be empty if survey has no questions)
                  }
                - On failure: {
                    "success": False,
                    "error": str  # Explanation (e.g., survey does not exist)
                  }

        Constraints:
            - Survey must exist.
            - Only questions linked to that survey are included.
            - Results are ordered as per the 'order' field.
        """
        if survey_id not in self.surveys:
            return { "success": False, "error": "Survey does not exist" }
    
        questions = [
            question_info for question_info in self.questions.values()
            if question_info["survey_id"] == survey_id
        ]
        sorted_questions = sorted(questions, key=lambda q: q["order"])
    
        return { "success": True, "data": sorted_questions }

    def get_options_by_question(self, question_id: str) -> dict:
        """
        Retrieve all options for a specific question, in their display order.

        Args:
            question_id (str): The unique identifier of the question.

        Returns:
            dict: {
                "success": True,
                "data": List[OptionInfo]  # All options for the question, sorted by 'order'
            }
            OR
            {
                "success": False,
                "error": str  # e.g., 'Question does not exist'
            }

        Constraints:
            - The question must exist.
            - All returned options must reference the given question and be sorted by the 'order' attribute.
        """
        if question_id not in self.questions:
            return { "success": False, "error": "Question does not exist" }
    
        options_for_question = [
            option for option in self.options.values() if option["question_id"] == question_id
        ]
        # Sort options by their 'order'
        options_for_question.sort(key=lambda x: x.get("order", 0))
        return { "success": True, "data": options_for_question }

    def get_question_by_id(self, question_id: str) -> dict:
        """
        Retrieve information about a specific question.

        Args:
            question_id (str): The unique identifier of the question to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": QuestionInfo  # All metadata fields for the question
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., "Question not found"
            }

        Constraints:
            - The question_id must exist in the questions dictionary.
        """
        question = self.questions.get(question_id)
        if question is None:
            return { "success": False, "error": "Question not found" }
        return { "success": True, "data": question }

    def get_option_by_id(self, option_id: str) -> dict:
        """
        Retrieve the details of an option by its option_id.

        Args:
            option_id (str): The unique identifier of the option.

        Returns:
            dict:
                On success: {"success": True, "data": OptionInfo}
                On failure: {"success": False, "error": str}

        Constraints:
            - option_id must exist in the system.
        """
        option = self.options.get(option_id)
        if option is None:
            return {"success": False, "error": "Option not found"}
        return {"success": True, "data": option}

    def get_questions_and_options_for_survey(self, survey_id: str) -> dict:
        """
        Retrieve the full set of questions and their options for the specified survey,
        providing both questions and options in their correct order.

        Args:
            survey_id (str): The ID of the survey.

        Returns:
            dict: {
                "success": True,
                "data": List[{
                    "question": QuestionInfo,
                    "options": List[OptionInfo],  # ordered
                }]
            }
            or {
                "success": False,
                "error": str
            }

        Constraints:
            - survey_id must exist in the system.
            - questions and options must be provided in their specified order.
        """
        if survey_id not in self.surveys:
            return {"success": False, "error": "Survey not found"}

        # Select all questions for this survey
        questions = [
            question for question in self.questions.values()
            if question["survey_id"] == survey_id
        ]
        questions.sort(key=lambda q: q["order"])

        result = []
        for question in questions:
            qid = question["question_id"]
            options = [
                option for option in self.options.values()
                if option["question_id"] == qid
            ]
            options.sort(key=lambda o: o["order"])
            result.append({
                "question": question,
                "options": options
            })

        return {"success": True, "data": result}

    def list_participants_for_survey(self, survey_id: str) -> dict:
        """
        List all participants (ParticipantInfo) who have submitted a response to the specified survey.

        Args:
            survey_id (str): The ID of the survey.

        Returns:
            dict:
              - On success: { "success": True, "data": List[ParticipantInfo] }
              - On error:   { "success": False, "error": str }
        Constraints:
            - survey_id must identify an existing survey.
            - Only distinct participants who have submitted responses to this survey are listed.
        """
        if survey_id not in self.surveys:
            return {"success": False, "error": "Survey does not exist"}

        # Collect unique participant_ids who responded to this survey
        participant_ids = {
            resp["participant_id"]
            for resp in self.responses.values()
            if resp["survey_id"] == survey_id
        }

        # Retrieve valid ParticipantInfo objects
        participant_list = [
            self.participants[pid]
            for pid in participant_ids
            if pid in self.participants  # Defensive: only if participant still exists
        ]

        return {"success": True, "data": participant_list}

    def get_participant_by_id(self, participant_id: str) -> dict:
        """
        Retrieve detailed info for a participant, including user_id and demographic info.

        Args:
            participant_id (str): The unique ID of the participant.

        Returns:
            dict: {
                "success": True,
                "data": ParticipantInfo   # Detailed info for the participant
            }
            or
            {
                "success": False,
                "error": str              # Reason for failure (e.g., not found)
            }

        Constraints:
            - participant_id must exist in the system.
        """
        participant = self.participants.get(participant_id)
        if participant is None:
            return { "success": False, "error": "Participant not found" }
        return { "success": True, "data": participant }

    def get_responses_by_participant(self, participant_id: str) -> dict:
        """
        Retrieve all submitted responses for a participant across all surveys.

        Args:
            participant_id (str): The unique participant ID.

        Returns:
            dict: {
                "success": True,
                "data": List[ResponseInfo]  # List of all responses submitted by this participant (could be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., participant not found
            }

        Constraints:
            - The participant must exist in the system.
        """
        if participant_id not in self.participants:
            return {"success": False, "error": "Participant not found"}

        responses = [
            resp for resp in self.responses.values()
            if resp["participant_id"] == participant_id
        ]
        return {"success": True, "data": responses}

    def get_responses_by_survey(self, survey_id: str) -> dict:
        """
        Retrieve all responses given to a specific survey.

        Args:
            survey_id (str): The ID of the survey whose responses should be listed.

        Returns:
            dict: 
                - If survey exists: {"success": True, "data": List[ResponseInfo]}
                - If survey does not exist: {"success": False, "error": "Survey does not exist"}
        Constraints:
            - The survey must exist in the system.
        """
        if survey_id not in self.surveys:
            return {"success": False, "error": "Survey does not exist"}

        responses = [
            resp for resp in self.responses.values()
            if resp["survey_id"] == survey_id
        ]
        return {"success": True, "data": responses}

    def get_aggregated_results_for_survey(self, survey_id: str) -> dict:
        """
        Retrieve the aggregated response data for a survey (counts per option/question).

        Args:
            survey_id (str): The ID of the survey to query.

        Returns:
            dict:
                - {"success": True, "data": List[AggregatedResultInfo]}: on success (possibly empty list)
                - {"success": False, "error": str}: if the survey does not exist

        Constraints:
            - survey_id must exist in the system.
        """
        if survey_id not in self.surveys:
            return {"success": False, "error": "Survey not found"}

        results = [
            agg_info for key, agg_info in self.aggregated_results.items()
            if key[0] == survey_id
        ]
        return {"success": True, "data": results}

    def get_survey_status(self, survey_id: str) -> dict:
        """
        Retrieve the current status ('draft', 'published', 'closed', etc.) of a survey.

        Args:
            survey_id (str): The unique identifier of the survey.

        Returns:
            dict:
                - If found: { "success": True, "data": status }
                - If not found: { "success": False, "error": "Survey not found" }

        Constraints:
            - The survey with the specified survey_id must exist in the system.
        """
        survey = self.surveys.get(survey_id)
        if not survey:
            return { "success": False, "error": "Survey not found" }
        status = survey.get("status")
        return { "success": True, "data": status }

    def create_survey(
        self,
        survey_id: str,
        title: str,
        description: str,
        creator_id: str,
        created_at: str,
        status: str
    ) -> dict:
        """
        Create and register a new survey with the provided metadata.

        Args:
            survey_id (str): Unique ID for the new survey.
            title (str): The survey title.
            description (str): Survey description.
            creator_id (str): ID of the creator user.
            created_at (str): ISO8601 or timestamp string of creation time.
            status (str): Survey status; one of 'draft', 'published', 'closed'.

        Returns:
            dict: {
                "success": True,
                "message": "Survey created successfully."
            }
            or
            {
                "success": False,
                "error": "reason for failure"
            }
        Constraints:
            - survey_id must be unique.
            - All required fields must be provided (not empty).
            - status must be one of 'draft', 'published', 'closed'.
        """
        required_statuses = {'draft', 'published', 'closed'}
        # Check uniqueness
        if survey_id in self.surveys:
            return {"success": False, "error": "Survey ID already exists."}
        # Field checks
        if not (survey_id and title and creator_id and created_at and status):
            return {"success": False, "error": "Missing required survey metadata."}
        # Status validation
        if status not in required_statuses:
            return {"success": False, "error": f"Invalid status value: {status}"}

        survey_info: SurveyInfo = {
            "survey_id": survey_id,
            "title": title,
            "description": description,
            "creator_id": creator_id,
            "created_at": created_at,
            "status": status
        }
        self.surveys[survey_id] = survey_info
        return {"success": True, "message": "Survey created successfully."}

    def update_survey_status(self, survey_id: str, new_status: str) -> dict:
        """
        Change the status of a survey (e.g., from draft to published or closed).

        Args:
            survey_id (str): The unique ID of the survey to update.
            new_status (str): The new status value ('draft', 'published', 'closed').

        Returns:
            dict: 
              - success: True and a message if the update succeeds.
              - success: False and an error message if the operation fails (e.g., survey not found, invalid status).

        Constraints:
            - survey_id must exist in the system.
            - new_status must be one of the allowed status values for surveys ('draft', 'published', 'closed').
        """
        allowed_statuses = {'draft', 'published', 'closed'}

        if survey_id not in self.surveys:
            return {"success": False, "error": "Survey not found."}

        if new_status not in allowed_statuses:
            return {"success": False, "error": "Invalid survey status. Allowed values: draft, published, closed."}

        self.surveys[survey_id]['status'] = new_status
        return {"success": True, "message": f"Survey status updated to {new_status}."}

    def add_question_to_survey(
        self, 
        survey_id: str, 
        question_id: str, 
        text: str, 
        type: str, 
        order: int
    ) -> dict:
        """
        Add a new question to a specified survey at the given position/order.

        Args:
            survey_id (str): The ID of the survey to add the question to.
            question_id (str): Unique ID for this new question.
            text (str): The question's content/text.
            type (str): Type of question ('single-choice', 'multiple-choice', etc.).
            order (int): Position of the question in the survey.

        Returns:
            dict:
                - success: True/False
                - message: If success
                - error: If failed, error message

        Constraints:
            - survey_id must exist and be in 'draft' status.
            - question_id must be unique (not already used).
            - order in that survey's question list must not duplicate another.
            - Each question belongs to one and only one survey.
        """
        # Check survey existence and status
        survey = self.surveys.get(survey_id)
        if not survey:
            return { "success": False, "error": "Survey does not exist" }
        if survey["status"] != "draft":
            return { "success": False, "error": "Can only edit questions in draft surveys" }

        # Check unique question_id
        if question_id in self.questions:
            return { "success": False, "error": "Question ID already exists" }

        # Check text/type validity
        if not text or not text.strip():
            return { "success": False, "error": "Question text cannot be empty" }
        if not type or not type.strip():
            return { "success": False, "error": "Question type cannot be empty" }

        # Check order uniqueness within the survey
        for q in self.questions.values():
            if q["survey_id"] == survey_id and q["order"] == order:
                return { "success": False, "error": "Order already used for another question in this survey" }

        # Add the new question
        question_info = QuestionInfo(
            question_id=question_id,
            survey_id=survey_id,
            text=text,
            type=type,
            order=order
        )
        self.questions[question_id] = question_info

        return { "success": True, "message": "Question added to survey." }

    def update_question_text(self, question_id: str, new_text: str) -> dict:
        """
        Edit the text of a question.

        Args:
            question_id (str): The unique ID of the question to update.
            new_text (str): The new text for the question.

        Returns:
            dict: {
                "success": True,
                "message": "Question text updated."
            }
            or
            {
                "success": False,
                "error": "Reason for failure."
            }

        Constraints:
            - question_id must exist in the system.
            - new_text must be non-empty (not just whitespace).
        """
        if question_id not in self.questions:
            return { "success": False, "error": "Question not found." }
        if not isinstance(new_text, str) or not new_text.strip():
            return { "success": False, "error": "New text must be non-empty." }

        self.questions[question_id]["text"] = new_text.strip()
        return { "success": True, "message": "Question text updated." }

    def add_option_to_question(
        self,
        question_id: str,
        text: str,
        order: int = None
    ) -> dict:
        """
        Add a new selectable option to a given question, preserving or assigning order.

        Args:
            question_id (str): The question to attach the option to.
            text (str): Text of the new option.
            order (Optional[int]): 1-based order for insertion (if None, append at end).

        Returns:
            dict:
              Success: {
                  "success": True,
                  "message": "Option added to question <question_id> with option_id <option_id>"
              }
              Failure: {
                  "success": False,
                  "error": <reason>
              }

        Constraints:
            - question_id must exist.
            - Option added must preserve question's option ordering.
            - Option's 'order' must be valid (between 1 and #options+1 if supplied).
        """
        # Ensure the question exists
        if question_id not in self.questions:
            return {"success": False, "error": "Question does not exist"}

        # Gather current options for the question, ordered
        current_options = [opt for opt in self.options.values() if opt["question_id"] == question_id]
        current_options_sorted = sorted(current_options, key=lambda x: x["order"])
        num_options = len(current_options_sorted)

        # Default: append
        if order is None:
            insert_order = num_options + 1  # 1-based order, next available spot
        else:
            if order < 1 or order > num_options + 1:
                return {"success": False, "error": f"Order must be between 1 and {num_options + 1}"}
            insert_order = order

        # Shift down option order for options at or after 'order'
        for opt in current_options_sorted[::-1]:  # Reverse for stable shifting
            if opt["order"] >= insert_order:
                opt["order"] += 1
                self.options[opt["option_id"]]["order"] = opt["order"]

        # Generate new option_id (simple UUID or incremental for demo)
        option_id = str(uuid.uuid4())

        # Add new option
        self.options[option_id] = {
            "option_id": option_id,
            "question_id": question_id,
            "text": text,
            "order": insert_order
        }

        return {
            "success": True,
            "message": f"Option added to question {question_id} with option_id {option_id}"
        }

    def update_option_text(self, option_id: str, new_text: str) -> dict:
        """
        Edit the text of an existing option.

        Args:
            option_id (str): ID of the option to update.
            new_text (str): The new text to set for the option.

        Returns:
            dict: {
                "success": True,
                "message": "Option text updated."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Option must exist.
            - Option's parent question and survey must exist.
            - Option cannot be edited if the parent survey is closed.
        """
        option = self.options.get(option_id)
        if not option:
            return { "success": False, "error": "Option not found." }

        question_id = option["question_id"]
        question = self.questions.get(question_id)
        if not question:
            return { "success": False, "error": "Parent question not found." }

        survey_id = question["survey_id"]
        survey = self.surveys.get(survey_id)
        if not survey:
            return { "success": False, "error": "Parent survey not found." }

        if survey["status"] == "closed":
            return { "success": False, "error": "Cannot edit option for closed survey." }

        self.options[option_id]["text"] = new_text

        return { "success": True, "message": "Option text updated." }

    def register_participant(
        self, 
        participant_id: str, 
        user_id: Optional[str] = None, 
        demographic_info: Optional[dict] = None
    ) -> dict:
        """
        Add a new participant (user or anonymous) to the system.

        Args:
            participant_id (str): Unique identifier for the participant.
            user_id (Optional[str]): User account id, or None for anonymous participant.
            demographic_info (Optional[dict]): Optional demographic information.

        Returns:
            dict: {
                "success": True,
                "message": "Participant registered."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Each participant_id must be unique in the system.
        """
        if participant_id in self.participants:
            return {"success": False, "error": "Participant ID already exists."}

        participant_info: ParticipantInfo = {
            "participant_id": participant_id,
            "user_id": user_id,
            "demographic_info": demographic_info
        }
        # Remove None fields (as ParticipantInfo is total=False)
        participant_info = {k: v for k, v in participant_info.items() if v is not None}

        self.participants[participant_id] = participant_info
        return {"success": True, "message": "Participant registered."}


    def submit_response(
        self,
        participant_id: str,
        survey_id: str,
        question_id: str,
        selected_option_id: str,
        answered_at: str
    ) -> dict:
        """
        Record a participant’s answer to a question, enforcing:
        - Survey must exist and be published.
        - Participant must exist.
        - Question must belong to the survey.
        - Option must belong to the question.
        - Only one response per question per participant and survey.

        Args:
            participant_id (str): The responding participant's ID.
            survey_id (str): The ID of the survey being answered.
            question_id (str): The ID of the question being answered.
            selected_option_id (str): The ID of the selected option.
            answered_at (str): Timestamp string when answer was submitted.

        Returns:
            dict: 
              - On success: { "success": True, "message": "Response recorded" }.
              - On error: { "success": False, "error": "<reason>" }.
        """

        # 1. Check participant exists
        if participant_id not in self.participants:
            return { "success": False, "error": "Participant does not exist" }

        # 2. Check survey exists and is published
        survey = self.surveys.get(survey_id)
        if survey is None:
            return { "success": False, "error": "Survey does not exist" }
        if survey.get("status") != "published":
            return { "success": False, "error": "Survey is not published" }

        # 3. Check question exists and belongs to the survey
        question = self.questions.get(question_id)
        if question is None:
            return { "success": False, "error": "Question does not exist" }
        if question.get("survey_id") != survey_id:
            return { "success": False, "error": "Question does not belong to the given survey" }

        # 4. Check option exists and belongs to the question
        option = self.options.get(selected_option_id)
        if option is None:
            return { "success": False, "error": "Option does not exist" }
        if option.get("question_id") != question_id:
            return { "success": False, "error": "Option does not belong to the given question" }

        # 5. Check for duplicate response by participant to the same survey/question
        for resp in self.responses.values():
            if (
                resp["participant_id"] == participant_id and
                resp["survey_id"] == survey_id and
                resp["question_id"] == question_id
            ):
                return { "success": False, "error": "Participant has already responded to this question in this survey" }

        # 6. Record the response (generate unique response_id)
        response_id = str(uuid.uuid4())
        response_info = {
            "response_id": response_id,
            "participant_id": participant_id,
            "survey_id": survey_id,
            "question_id": question_id,
            "selected_option_id": selected_option_id,
            "answered_at": answered_at
        }
        self.responses[response_id] = response_info

        return { "success": True, "message": "Response recorded" }


    def update_response(self, response_id: str, new_selected_option_id: str) -> dict:
        """
        Update a participant's previous response to a new selected option for the same question,
        if survey rules permit.

        Args:
            response_id (str): The unique identifier of the response to update.
            new_selected_option_id (str): The option id to set as the new selection.

        Returns:
            dict:
                - On success: { "success": True, "message": "Response updated." }
                - On failure: { "success": False, "error": "reason" }

        Constraints:
            - Response must exist.
            - Survey must exist and be 'published'.
            - Survey must allow response updating (SurveyInfo['allow_update_response'] == True).
            - New option must belong to the same question as original response.
            - Aggregated results must be updated accordingly.
        """
        # Check response existence
        resp = self.responses.get(response_id)
        if not resp:
            return { "success": False, "error": "Response does not exist." }

        survey_id = resp['survey_id']
        question_id = resp['question_id']
        participant_id = resp['participant_id']
        old_option_id = resp['selected_option_id']

        # Check survey existence and status
        survey = self.surveys.get(survey_id)
        if not survey:
            return { "success": False, "error": "Survey does not exist." }
        if survey['status'] != 'published':
            return { "success": False, "error": "Survey is not published; responses cannot be changed." }

        # Check if survey allows updating responses
        allow_update = survey.get('allow_update_response', False)
        if not allow_update:
            return { "success": False, "error": "Updating responses is not permitted for this survey." }

        # Check new option existence and that it matches the question
        new_option = self.options.get(new_selected_option_id)
        if not new_option or new_option['question_id'] != question_id:
            return { "success": False, "error": "Invalid option for the corresponding question." }

        # If no actual change, consider success (for idempotency)
        if old_option_id == new_selected_option_id:
            return { "success": True, "message": "No change: the response is already set to this option." }

        # Update response record
        resp['selected_option_id'] = new_selected_option_id
        resp['answered_at'] = datetime.utcnow().isoformat()

        # Update aggregated results:
        old_key = (survey_id, question_id, old_option_id)
        new_key = (survey_id, question_id, new_selected_option_id)
        # Decrement old
        if old_key in self.aggregated_results:
            self.aggregated_results[old_key]['response_count'] = max(
                0, self.aggregated_results[old_key]['response_count'] - 1)
        # Increment new
        if new_key not in self.aggregated_results:
            self.aggregated_results[new_key] = {
                'survey_id': survey_id,
                'question_id': question_id,
                'option_id': new_selected_option_id,
                'response_count': 1
            }
        else:
            self.aggregated_results[new_key]['response_count'] += 1

        return { "success": True, "message": "Response updated." }

    def recompute_aggregated_results(self, survey_id: str) -> dict:
        """
        Recalculate and refresh the aggregated response counts for all questions and options within a given survey.
    
        Args:
            survey_id (str): The ID of the survey for which to recompute aggregated results.

        Returns:
            dict: 
              - On success:
                    { "success": True, "message": "Aggregated results recomputed for survey <survey_id>." }
              - On failure:
                    { "success": False, "error": "Survey does not exist" }

        Constraints:
            - Survey must exist.
            - Only options and questions that currently belong to the survey are considered.
            - Results are recalculated from current responses.
        """
        if survey_id not in self.surveys:
            return { "success": False, "error": "Survey does not exist" }

        # Collect all questions for this survey
        questions_for_survey = [
            q for q in self.questions.values()
            if q["survey_id"] == survey_id
        ]
        # Build set of valid (question_id, option_id) pairs for survey
        valid_pairs = set()
        for q in questions_for_survey:
            options_for_question = [
                o for o in self.options.values() if o["question_id"] == q["question_id"]
            ]
            for o in options_for_question:
                valid_pairs.add((q["question_id"], o["option_id"]))

        # Clear out old aggregated results for this survey that are no longer valid or stale
        stale_keys = [
            key for key in self.aggregated_results
            if key[0] == survey_id and (key[1], key[2]) not in valid_pairs
        ]
        for key in stale_keys:
            del self.aggregated_results[key]

        # Now (re)compute response counts for all valid (question, option) pairs
        # First: Group responses for this survey by (question_id, option_id)
        response_counter = {}  # (question_id, option_id): count
        for response in self.responses.values():
            if response["survey_id"] == survey_id:
                qid = response["question_id"]
                oid = response["selected_option_id"]
                if (qid, oid) in valid_pairs:
                    response_counter[(qid, oid)] = response_counter.get((qid, oid), 0) + 1

        # For each valid pair, update aggregated_results
        for (qid, oid) in valid_pairs:
            count = response_counter.get((qid, oid), 0)
            key = (survey_id, qid, oid)
            self.aggregated_results[key] = {
                "survey_id": survey_id,
                "question_id": qid,
                "option_id": oid,
                "response_count": count
            }

        return {
            "success": True,
            "message": f"Aggregated results recomputed for survey {survey_id}."
        }

    def reorder_questions_in_survey(self, survey_id: str, ordered_question_ids: list) -> dict:
        """
        Change the sort order of questions within a given survey.
    
        Args:
            survey_id (str): ID of the survey.
            ordered_question_ids (List[str]): List of question IDs in the desired new order.
                The list must contain all and only the question IDs of the survey, no more, no less (no duplicates).
    
        Returns:
            dict:
                - On success: { "success": True, "message": "Questions reordered successfully." }
                - On failure: { "success": False, "error": <reason> }
    
        Constraints:
            - Survey must exist.
            - All question_ids must exist and belong to the specified survey.
            - Must not omit or duplicate questions.
            - Updates the `order` field on each question.
        """
        # Check that survey exists
        if survey_id not in self.surveys:
            return { "success": False, "error": "Survey does not exist." }
    
        # Collect all question IDs currently in the survey
        survey_question_ids = [qid for qid, q in self.questions.items() if q["survey_id"] == survey_id]
        survey_question_set = set(survey_question_ids)
        incoming_question_set = set(ordered_question_ids)
    
        # Check for duplicates
        if len(ordered_question_ids) != len(set(ordered_question_ids)):
            return { "success": False, "error": "Duplicate question IDs in ordering." }
    
        # Check that sets match
        if survey_question_set != incoming_question_set:
            return { 
                "success": False,
                "error": "Provided question IDs do not exactly match survey's questions."
            }
    
        # Further check: ensure all IDs actually exist and belong
        for question_id in ordered_question_ids:
            if question_id not in self.questions:
                return { "success": False, "error": f"Question ID {question_id} does not exist." }
            if self.questions[question_id]["survey_id"] != survey_id:
                return { "success": False, "error": f"Question ID {question_id} does not belong to the survey." }
    
        # Update order fields
        for idx, question_id in enumerate(ordered_question_ids):
            self.questions[question_id]["order"] = idx + 1  # 1-based order
    
        return {"success": True, "message": "Questions reordered successfully."}

    def reorder_options_in_question(self, question_id: str, new_order: list) -> dict:
        """
        Change the sort order of options for a given question.

        Args:
            question_id (str): The question whose options are to be reordered.
            new_order (list of str): List of option_ids, ordered as desired (from first to last).

        Returns:
            dict: {
                "success": True,
                "message": "Options reordered successfully."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
        - question_id must exist in the system.
        - new_order must contain exactly (and only) all option_ids for the given question (no missing, extra, or duplicates).
        - Option sorting is considered by the `order` field of each OptionInfo.
        """
        # Check existence of question
        if question_id not in self.questions:
            return { "success": False, "error": "Question does not exist." }

        # Get all options for this question
        option_ids = [oid for oid, opt in self.options.items() if opt['question_id'] == question_id]
        if not option_ids:
            # It is still possible, but nothing to reorder
            if new_order:
                return {"success": False, "error": "No options exist for the given question."}
            else:
                return {"success": True, "message": "No options to reorder."}

        # Check that new_order covers all and only these ids, with no duplicates
        if set(new_order) != set(option_ids) or len(new_order) != len(option_ids):
            return {
                "success": False,
                "error": "new_order must include exactly all option_ids for the question, no extra/missing/duplicate IDs."
            }

        # Assign new order: order = 1-based index
        for idx, option_id in enumerate(new_order):
            self.options[option_id]['order'] = idx + 1

        return {
            "success": True,
            "message": "Options reordered successfully."
        }

    def delete_survey(self, survey_id: str) -> dict:
        """
        Remove an entire survey and all its associated data, including:
        - All questions belonging to the survey
        - All options belonging to those questions
        - All responses for the survey
        - All aggregated results for the survey

        Args:
            survey_id (str): The unique identifier of the survey to delete.

        Returns:
            dict:
                - On success: {"success": True, "message": "Survey <survey_id> and associated data deleted."}
                - On failure: {"success": False, "error": <reason>}

        Constraints:
            - Cannot delete a survey that does not exist.
            - All related data must be removed (no orphaned questions, options, responses, or aggregates).
        """
        # Check if the survey exists
        if survey_id not in self.surveys:
            return { "success": False, "error": "Survey does not exist." }

        # Find all question_ids for this survey
        question_ids = [q_id for q_id, q in self.questions.items() if q['survey_id'] == survey_id]

        # Find all option_ids for these questions
        option_ids = [o_id for o_id, o in self.options.items() if o['question_id'] in question_ids]

        # Delete responses for this survey
        to_delete_response_ids = [r_id for r_id, r in self.responses.items() if r['survey_id'] == survey_id]
        for r_id in to_delete_response_ids:
            del self.responses[r_id]

        # Delete aggregated results for this survey
        to_delete_agg_keys = [key for key in self.aggregated_results if key[0] == survey_id]
        for key in to_delete_agg_keys:
            del self.aggregated_results[key]

        # Delete options for these questions
        for o_id in option_ids:
            del self.options[o_id]

        # Delete questions for this survey
        for q_id in question_ids:
            del self.questions[q_id]

        # Delete the survey itself
        del self.surveys[survey_id]

        return { 
            "success": True, 
            "message": f"Survey {survey_id} and all associated data deleted." 
        }

    def delete_question(self, question_id: str) -> dict:
        """
        Remove a specific question (and associated options, responses, aggregated results) from the survey.

        Args:
            question_id (str): The ID of the question to delete.

        Returns:
            dict: {
                "success": True, "message": "Question deleted."
            }
            or
            {
                "success": False, "error": <reason>
            }

        Constraints:
            - The question must exist.
            - All associated options, responses, and aggregated results are also deleted.
            - Integrity: Do not delete the parent survey.
        """
        if question_id not in self.questions:
            return { "success": False, "error": "Question does not exist." }

        # Collect option_ids for this question
        option_ids_to_delete = [oid for oid, oinfo in self.options.items() if oinfo["question_id"] == question_id]

        # Remove options for this question
        for option_id in option_ids_to_delete:
            del self.options[option_id]

        # Remove responses for this question
        response_ids_to_delete = [rid for rid, rinfo in self.responses.items() if rinfo["question_id"] == question_id]
        for response_id in response_ids_to_delete:
            del self.responses[response_id]

        # Remove aggregated results for this question
        keys_to_delete = [key for key in self.aggregated_results if key[1] == question_id]
        for key in keys_to_delete:
            del self.aggregated_results[key]

        # Finally, delete the question
        del self.questions[question_id]

        return { "success": True, "message": "Question deleted." }

    def delete_option(self, option_id: str) -> dict:
        """
        Remove a specific option from a question, with integrity checks.

        Args:
            option_id (str): The unique identifier of the option to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Option <option_id> deleted."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Option must exist.
            - Cannot delete if any response references this option.
            - Removes related aggregated results.
            - (Optionally) reorders the remaining options for the question to maintain order continuity.
        """
        if option_id not in self.options:
            return {"success": False, "error": "Option does not exist."}

        # Check for existing responses referencing this option
        found_responses = [
            r for r in self.responses.values()
            if r['selected_option_id'] == option_id
        ]
        if found_responses:
            return {
                "success": False,
                "error": "Cannot delete option because there are responses referencing it."
            }

        option_info = self.options[option_id]
        question_id = option_info['question_id']

        # Remove the option itself
        del self.options[option_id]

        # Remove associated aggregated results
        to_delete_agg = [
            key for key in self.aggregated_results
            if key[2] == option_id  # (survey_id, question_id, option_id)
        ]
        for key in to_delete_agg:
            del self.aggregated_results[key]

        # Reorder: ensure options' 'order' values for the question remain contiguous (optional but good)
        other_options = [
            o for o in self.options.values() if o['question_id'] == question_id
        ]
        other_options_sorted = sorted(other_options, key=lambda o: o['order'])
        for idx, o in enumerate(other_options_sorted, 1):
            o['order'] = idx

        return {"success": True, "message": f"Option {option_id} deleted."}

    def delete_participant(self, participant_id: str) -> dict:
        """
        Remove a participant and all their responses from the system.

        Args:
            participant_id (str): The ID of the participant to remove.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Participant and all their responses deleted."
                    }
                On failure (participant not found):
                    {
                        "success": False,
                        "error": "Participant does not exist"
                    }

        Constraints:
            - Participant must exist.
            - All responses referencing this participant must be removed.
        """
        if participant_id not in self.participants:
            return { "success": False, "error": "Participant does not exist" }

        # Find response_ids to delete
        response_ids_to_delete = [resp_id for resp_id, resp in self.responses.items()
                                  if resp["participant_id"] == participant_id]

        for resp_id in response_ids_to_delete:
            del self.responses[resp_id]

        del self.participants[participant_id]

        return { "success": True, "message": "Participant and all their responses deleted." }

    def delete_response(self, response_id: str) -> dict:
        """
        Remove a specific participant response by its response_id from the system.

        Args:
            response_id (str): The unique identifier of the response to be removed.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Response deleted successfully."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Response not found."
                    }
        Constraints:
            - Response must exist.
            - If aggregated results are maintained, decrement the relevant response count.
        """
        response = self.responses.get(response_id)
        if not response:
            return {"success": False, "error": "Response not found."}

        # Update aggregated_results if it exists for the survey/question/option
        survey_id = response["survey_id"]
        question_id = response["question_id"]
        option_id = response["selected_option_id"]
        agg_key = (survey_id, question_id, option_id)
    
        if agg_key in self.aggregated_results:
            agg = self.aggregated_results[agg_key]
            if agg["response_count"] > 0:
                agg["response_count"] -= 1
            # Optionally, remove if count becomes 0 (or just leave at 0 by instruction)
            self.aggregated_results[agg_key] = agg

        # Delete the response
        del self.responses[response_id]
        return {"success": True, "message": "Response deleted successfully."}


class OnlineSurveyManagementSystem(BaseEnv):
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
            if key == "aggregated_results" and isinstance(value, dict):
                normalized = {}
                for raw_key, raw_value in value.items():
                    item = copy.deepcopy(raw_value)
                    if isinstance(item, dict):
                        survey_id = item.get("survey_id")
                        question_id = item.get("question_id")
                        option_id = item.get("option_id")
                        if (
                            isinstance(survey_id, str)
                            and isinstance(question_id, str)
                            and isinstance(option_id, str)
                        ):
                            normalized[(survey_id, question_id, option_id)] = item
                            continue
                    normalized[raw_key] = item
                setattr(env, key, normalized)
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

    def get_survey_by_id(self, **kwargs):
        return self._call_inner_tool('get_survey_by_id', kwargs)

    def list_surveys(self, **kwargs):
        return self._call_inner_tool('list_surveys', kwargs)

    def get_questions_by_survey(self, **kwargs):
        return self._call_inner_tool('get_questions_by_survey', kwargs)

    def get_options_by_question(self, **kwargs):
        return self._call_inner_tool('get_options_by_question', kwargs)

    def get_question_by_id(self, **kwargs):
        return self._call_inner_tool('get_question_by_id', kwargs)

    def get_option_by_id(self, **kwargs):
        return self._call_inner_tool('get_option_by_id', kwargs)

    def get_questions_and_options_for_survey(self, **kwargs):
        return self._call_inner_tool('get_questions_and_options_for_survey', kwargs)

    def list_participants_for_survey(self, **kwargs):
        return self._call_inner_tool('list_participants_for_survey', kwargs)

    def get_participant_by_id(self, **kwargs):
        return self._call_inner_tool('get_participant_by_id', kwargs)

    def get_responses_by_participant(self, **kwargs):
        return self._call_inner_tool('get_responses_by_participant', kwargs)

    def get_responses_by_survey(self, **kwargs):
        return self._call_inner_tool('get_responses_by_survey', kwargs)

    def get_aggregated_results_for_survey(self, **kwargs):
        return self._call_inner_tool('get_aggregated_results_for_survey', kwargs)

    def get_survey_status(self, **kwargs):
        return self._call_inner_tool('get_survey_status', kwargs)

    def create_survey(self, **kwargs):
        return self._call_inner_tool('create_survey', kwargs)

    def update_survey_status(self, **kwargs):
        return self._call_inner_tool('update_survey_status', kwargs)

    def add_question_to_survey(self, **kwargs):
        return self._call_inner_tool('add_question_to_survey', kwargs)

    def update_question_text(self, **kwargs):
        return self._call_inner_tool('update_question_text', kwargs)

    def add_option_to_question(self, **kwargs):
        return self._call_inner_tool('add_option_to_question', kwargs)

    def update_option_text(self, **kwargs):
        return self._call_inner_tool('update_option_text', kwargs)

    def register_participant(self, **kwargs):
        return self._call_inner_tool('register_participant', kwargs)

    def submit_response(self, **kwargs):
        return self._call_inner_tool('submit_response', kwargs)

    def update_response(self, **kwargs):
        return self._call_inner_tool('update_response', kwargs)

    def recompute_aggregated_results(self, **kwargs):
        return self._call_inner_tool('recompute_aggregated_results', kwargs)

    def reorder_questions_in_survey(self, **kwargs):
        return self._call_inner_tool('reorder_questions_in_survey', kwargs)

    def reorder_options_in_question(self, **kwargs):
        return self._call_inner_tool('reorder_options_in_question', kwargs)

    def delete_survey(self, **kwargs):
        return self._call_inner_tool('delete_survey', kwargs)

    def delete_question(self, **kwargs):
        return self._call_inner_tool('delete_question', kwargs)

    def delete_option(self, **kwargs):
        return self._call_inner_tool('delete_option', kwargs)

    def delete_participant(self, **kwargs):
        return self._call_inner_tool('delete_participant', kwargs)

    def delete_response(self, **kwargs):
        return self._call_inner_tool('delete_response', kwargs)
