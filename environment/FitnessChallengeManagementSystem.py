# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



class UserInfo(TypedDict):
    _id: str
    name: str
    email: str
    account_status: str  # from 'account_sta'

class ChallengeInfo(TypedDict):
    challenge_id: str
    name: str
    description: str
    objectives: str
    timeline_start: str
    timeline_end: str
    progress_metrics: str
    status: str  # from 'sta'

class EnrollmentInfo(TypedDict):
    enrollment_id: str
    user_id: str
    challenge_id: str
    enrollment_date: str
    progress: str
    status: str  # from 'sta'

class _GeneratedEnvImpl:
    def __init__(self):
        """
        The environment for managing users, fitness challenges, and enrollments.
        """
        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Challenges: {challenge_id: ChallengeInfo}
        self.challenges: Dict[str, ChallengeInfo] = {}

        # Enrollments: {enrollment_id: EnrollmentInfo}
        # Each user can only have one active enrollment per challenge at a time.
        self.enrollments: Dict[str, EnrollmentInfo] = {}

        # Constraints:
        # - Each user can only be enrolled once in the same challenge at a time.
        # - Challenge details must be accessible for any user enrollment.
        # - Challenge status and user progress are updated based on events/actions.
        # - Challenge.status can be values like 'upcoming', 'active', 'completed', 'canceled'.

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve full user information given a user ID.

        Args:
            user_id (str): Unique user identifier.

        Returns:
            dict:
                - On success: {'success': True, 'data': UserInfo}
                - If user not found: {'success': False, 'error': 'User not found'}
        """
        user_info = self.users.get(user_id)
        if user_info is not None:
            return {"success": True, "data": user_info}
        else:
            return {"success": False, "error": "User not found"}

    def get_user_by_name(self, name: str) -> dict:
        """
        Retrieve full user information given the user's name.

        Args:
            name (str): The name of the user to search for.

        Returns:
            dict: {
                "success": True,
                "data": List[UserInfo]  # All users whose 'name' matches exactly (may be empty)
            }
            or
            {
                "success": False,
                "error": str
            }
        Constraints:
            - Name matching is case-sensitive and exact.
            - Name may not be unique; all matching users are returned.
        """
        if not isinstance(name, str):
            return { "success": False, "error": "Parameter 'name' must be a string." }

        results = [
            user_info for user_info in self.users.values()
            if user_info["name"] == name
        ]
        return { "success": True, "data": results }

    def get_enrollments_by_user_id(self, user_id: str) -> dict:
        """
        List all challenge enrollments (EnrollmentInfo) for a specific user.

        Args:
            user_id (str): Unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": List[EnrollmentInfo]  # List of all enrollments for the user (empty if none)
            }
            or
            {
                "success": False,
                "error": str  # Explanation if user does not exist
            }

        Constraints:
            - The user must exist in the system.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        enrollments = [
            enrollment
            for enrollment in self.enrollments.values()
            if enrollment["user_id"] == user_id
        ]

        return {"success": True, "data": enrollments}

    def get_active_enrollments_by_user_id(self, user_id: str) -> dict:
        """
        List all active (not completed or cancelled) challenge enrollments for a user.

        Args:
            user_id (str): The ID of the user.

        Returns:
            dict: {
                "success": True,
                "data": List[EnrollmentInfo],  # All the user's active enrollments (may be empty).
            }
            or
            {
                "success": False,
                "error": str  # If the user does not exist.
            }

        Constraints:
            - Only returns enrollments with status not in ('completed', 'canceled').
            - Returns empty list if user has no such enrollments.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }

        active_statuses = {'active', 'upcoming'}  # Usually 'active' and 'upcoming' are the 'active' ones.
        results = [
            enrollment for enrollment in self.enrollments.values()
            if enrollment['user_id'] == user_id and enrollment['status'] in active_statuses
        ]
        return { "success": True, "data": results }

    def get_challenge_by_id(self, challenge_id: str) -> dict:
        """
        Retrieve details for a specific challenge by challenge_id.

        Args:
            challenge_id (str): The unique identifier of the challenge.

        Returns:
            dict: {
                "success": True,
                "data": ChallengeInfo  # The challenge information.
            }
            OR
            {
                "success": False,
                "error": str  # Reason, e.g., challenge not found
            }

        Constraints:
            - The challenge with the given ID must exist in the system.
        """
        challenge = self.challenges.get(challenge_id)
        if not challenge:
            return { "success": False, "error": "Challenge not found" }
        return { "success": True, "data": challenge }

    def get_challenge_details_for_user(self, user_id: str) -> dict:
        """
        Retrieve challenge details (objectives, timelines, description, status, etc.)
        for all challenges in which the specified user is currently enrolled.

        Args:
            user_id (str): The identifier of the user.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[ChallengeInfo],  # List of challenge info dicts. May be empty if no current enrollments.
                }
                OR
                {
                    "success": False,
                    "error": str  # e.g. "User does not exist"
                }

        Constraints:
            - Only challenges where the user has an 'active' enrollment are considered.
            - If the user does not exist, returns error.
            - Omits challenges that cannot be found in the system for integrity.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
    
        # Find active enrollments for the user
        # Here, 'active' enrollment is assumed to have status == 'active'
        active_challenge_ids = [
            enrollment["challenge_id"]
            for enrollment in self.enrollments.values()
            if enrollment["user_id"] == user_id and enrollment["status"] == "active"
        ]
    
        # Get challenge details
        result = []
        for challenge_id in active_challenge_ids:
            challenge_info = self.challenges.get(challenge_id)
            if challenge_info:
                result.append(challenge_info)
    
        return { "success": True, "data": result }

    def get_enrollment_status(self, user_id: str, challenge_id: str) -> dict:
        """
        Query the enrollment status (e.g., 'active', 'canceled') of a user in a specific challenge.

        Args:
            user_id (str): ID of the user.
            challenge_id (str): ID of the challenge.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": {"status": <status_str>}
                    }
                On error:
                    {
                        "success": False,
                        "error": <reason>
                    }

        Constraints:
            - The user and challenge must exist.
            - There must be an enrollment for that user/challenge pair.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}
        if challenge_id not in self.challenges:
            return {"success": False, "error": "Challenge does not exist"}

        for enrollment in self.enrollments.values():
            if enrollment["user_id"] == user_id and enrollment["challenge_id"] == challenge_id:
                return {"success": True, "data": {"status": enrollment["status"]}}
    
        return {"success": False, "error": "Enrollment does not exist for user in this challenge"}

    def get_enrollment_progress(self, user_id: str, challenge_id: str) -> dict:
        """
        Retrieve the progress metrics for a user's enrollment in a specific challenge.

        Args:
            user_id (str): The unique identifier for the user.
            challenge_id (str): The unique identifier for the challenge.

        Returns:
            dict: 
                - On success: { "success": True, "data": str } # The progress value.
                - On failure: { "success": False, "error": str } # Reason, e.g. not enrolled.

        Constraints:
            - Only one enrollment per user per challenge is allowed at a time.
            - Both user_id and challenge_id must correspond to an existing enrollment.
        """
        for enrollment in self.enrollments.values():
            if enrollment["user_id"] == user_id and enrollment["challenge_id"] == challenge_id:
                return { "success": True, "data": enrollment["progress"] }

        return { "success": False, "error": "Enrollment not found" }

    def list_all_challenges(self) -> dict:
        """
        List all fitness challenges in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[ChallengeInfo]  # List of all challenges in the system (may be empty)
            }
        """
        all_challenges = list(self.challenges.values())
        return { "success": True, "data": all_challenges }

    def enroll_user_in_challenge(self, user_id: str, challenge_id: str) -> dict:
        """
        Enroll a user in a challenge if not currently enrolled. Respect the 
        constraint that a user cannot be enrolled more than once at a time per challenge.

        Args:
            user_id (str): The id of the user to enroll.
            challenge_id (str): The id of the challenge to enroll in.

        Returns:
            dict: {
                "success": True,
                "message": "User enrolled in challenge successfully."
            }
            or
            {
                "success": False,
                "error": "Error message."
            }
    
        Constraints:
            - User must exist.
            - Challenge must exist.
            - User must not already be enrolled in the challenge (active, upcoming, or in-progress).
        """

        # Check if user exists
        if user_id not in self.users:
            return {"success": False, "error": "User not found."}

        # Check if challenge exists
        if challenge_id not in self.challenges:
            return {"success": False, "error": "Challenge not found."}

        # Ensure the user is not already enrolled in this challenge in an overlapping status
        for enrollment in self.enrollments.values():
            if (
                enrollment["user_id"] == user_id 
                and enrollment["challenge_id"] == challenge_id
                and enrollment["status"] not in ["completed", "canceled"]
            ):
                return {"success": False, "error": "User already enrolled in this challenge."}

        # Generate a unique enrollment_id (simple scheme: f"{user_id}_{challenge_id}" + count-if-needed)
        base_id = f"{user_id}_{challenge_id}"
        eid = base_id
        counter = 1
        while eid in self.enrollments:
            eid = f"{base_id}_{counter}"
            counter += 1

        challenge = self.challenges[challenge_id]
        enrollment_info = {
            "enrollment_id": eid,
            "user_id": user_id,
            "challenge_id": challenge_id,
            "enrollment_date": challenge["timeline_start"],
            "progress": "0",  # Init as string, can be modified later
            "status": "active"
        }

        self.enrollments[eid] = enrollment_info

        return {"success": True, "message": "User enrolled in challenge successfully."}

    def update_enrollment_progress(self, enrollment_id: str, new_progress: str) -> dict:
        """
        Update the progress field of a user's enrollment in a specific challenge.

        Args:
            enrollment_id (str): The unique id of the enrollment to update.
            new_progress (str): The progress value to set (format is system-dependent).

        Returns:
            dict: {
                "success": True,
                "message": "Enrollment progress updated."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - The enrollment_id must exist.
            - The enrollment status must not be 'canceled' (and possibly not 'completed').
        """
        enrollment = self.enrollments.get(enrollment_id)
        if enrollment is None:
            return {"success": False, "error": "Enrollment not found."}
        
        # Do not update if the enrollment is 'canceled'
        if enrollment["status"].lower() == "canceled":
            return {"success": False, "error": "Cannot update progress for canceled enrollment."}
        
        # Optionally prevent update if status is 'completed'
        if enrollment["status"].lower() == "completed":
            return {"success": False, "error": "Cannot update progress for completed enrollment."}
    
        # Update progress
        enrollment["progress"] = new_progress
        return {"success": True, "message": "Enrollment progress updated."}

    def update_enrollment_status(self, enrollment_id: str, new_status: str) -> dict:
        """
        Update the status of a user's challenge enrollment.

        Args:
            enrollment_id (str): Unique identifier of the enrollment to update.
            new_status (str): The new status for the enrollment. Expected values include
                'active', 'completed', 'canceled', etc.

        Returns:
            dict: {
                "success": True,
                "message": "Enrollment status updated."
            }
            or
            {
                "success": False,
                "error": "Reason for failure."
            }

        Constraints:
            - Enrollment must exist.
            - Only valid statuses are accepted: ['active', 'completed', 'canceled', 'upcoming'].
        """
        allowed_statuses = {'active', 'completed', 'canceled', 'upcoming'}
    
        enrollment = self.enrollments.get(enrollment_id)
        if not enrollment:
            return {"success": False, "error": "Enrollment does not exist."}
    
        if new_status not in allowed_statuses:
            return {"success": False, "error": f"Invalid status: {new_status}."}
    
        if enrollment['status'] == new_status:
            return {"success": True, "message": "Enrollment status unchanged; already set to the requested status."}
    
        enrollment['status'] = new_status
        return {"success": True, "message": "Enrollment status updated."}

    def create_challenge(
        self,
        challenge_id: str,
        name: str,
        description: str,
        objectives: str,
        timeline_start: str,
        timeline_end: str,
        progress_metrics: str,
        status: str
    ) -> dict:
        """
        Create a new fitness challenge with the specified info.

        Args:
            challenge_id (str): Unique ID for the challenge.
            name (str): Challenge name.
            description (str): Challenge description.
            objectives (str): Objectives of the challenge.
            timeline_start (str): Start date/time (ISO format).
            timeline_end (str): End date/time (ISO format).
            progress_metrics (str): Info about how progress is tracked.
            status (str): Initial status, must be 'upcoming', 'active', 'completed', or 'canceled'.

        Returns:
            dict: {"success": True, "message": ...} or {"success": False, "error": ...}

        Constraints:
            - challenge_id must be unique.
            - status must be one of the allowed values.
            - All required fields must be non-empty.
        """
        allowed_statuses = {'upcoming', 'active', 'completed', 'canceled'}

        # Check if ID is unique
        if challenge_id in self.challenges:
            return {"success": False, "error": "Challenge ID already exists"}

        # Validate input fields
        if not (challenge_id and name and description and objectives and timeline_start and timeline_end and progress_metrics and status):
            return {"success": False, "error": "All challenge fields must be provided and non-empty"}

        if status not in allowed_statuses:
            return {"success": False, "error": f"Status '{status}' is invalid. Allowed: {', '.join(allowed_statuses)}"}

        new_challenge: ChallengeInfo = {
            "challenge_id": challenge_id,
            "name": name,
            "description": description,
            "objectives": objectives,
            "timeline_start": timeline_start,
            "timeline_end": timeline_end,
            "progress_metrics": progress_metrics,
            "status": status
        }

        self.challenges[challenge_id] = new_challenge

        return {"success": True, "message": f"Challenge {challenge_id} created successfully"}

    def update_challenge_status(self, challenge_id: str, new_status: str) -> dict:
        """
        Modify the status of a challenge (e.g., set to "active", "completed", or "canceled").

        Args:
            challenge_id (str): Unique identifier of the challenge to update.
            new_status   (str): New status ("upcoming", "active", "completed", "canceled").

        Returns:
            dict: {
                "success": True,
                "message": "Challenge status updated to <new_status>."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Challenge must exist.
            - new_status must be one of allowed status values.
        """
        allowed_statuses = {"upcoming", "active", "completed", "canceled"}

        if challenge_id not in self.challenges:
            return {"success": False, "error": "Challenge does not exist."}
        if new_status not in allowed_statuses:
            return {"success": False, "error": f"Invalid status value: {new_status}."}
    
        self.challenges[challenge_id]["status"] = new_status
        return {"success": True, "message": f"Challenge status updated to {new_status}."}

    def edit_challenge_info(
        self,
        challenge_id: str,
        name: str = None,
        description: str = None,
        objectives: str = None,
        timeline_start: str = None,
        timeline_end: str = None,
        progress_metrics: str = None,
        status: str = None
    ) -> dict:
        """
        Edit details (objectives, timeline, description, etc.) of an existing challenge.
    
        Args:
            challenge_id (str): The unique identifier of the challenge to edit.
            name (str, optional): New name for the challenge.
            description (str, optional): New description.
            objectives (str, optional): New objectives.
            timeline_start (str, optional): New timeline start.
            timeline_end (str, optional): New timeline end.
            progress_metrics (str, optional): New progress metrics.
            status (str, optional): New status for the challenge.

        Returns:
            dict: On success: {"success": True, "message": "Challenge info updated."}
                  On failure: {"success": False, "error": <reason>}
        
        Constraints:
            - The challenge with the provided challenge_id must exist.
            - Only valid fields can be updated; unknown fields are ignored.
            - If no valid fields are provided, no update occurs.
        """
        if challenge_id not in self.challenges:
            return {"success": False, "error": "Challenge does not exist."}

        challenge = self.challenges[challenge_id]
        editable_fields = {
            "name": name,
            "description": description,
            "objectives": objectives,
            "timeline_start": timeline_start,
            "timeline_end": timeline_end,
            "progress_metrics": progress_metrics,
            "status": status,
        }

        updated = False
        for field, value in editable_fields.items():
            if value is not None:
                challenge[field] = value
                updated = True

        if not updated:
            return {"success": False, "error": "No valid fields provided to update."}

        return {"success": True, "message": "Challenge info updated."}

    def cancel_enrollment(self, enrollment_id: str) -> dict:
        """
        Cancel a user's enrollment in a challenge.

        Args:
            enrollment_id (str): The unique identifier of the enrollment to cancel.

        Returns:
            dict:
                On success: { "success": True, "message": "Enrollment canceled successfully." }
                On failure: { "success": False, "error": str }

        Constraints:
            - The enrollment must exist.
            - The enrollment must not already be canceled.
            - On canceling, sets the enrollment's status to 'canceled'.
        """
        enrollment = self.enrollments.get(enrollment_id)
        if not enrollment:
            return { "success": False, "error": "Enrollment not found." }

        if enrollment["status"] == "canceled":
            return { "success": False, "error": "Enrollment is already canceled." }

        enrollment["status"] = "canceled"
        self.enrollments[enrollment_id] = enrollment

        return { "success": True, "message": "Enrollment canceled successfully." }

    def create_user(self, _id: str, name: str, email: str, account_status: str = "active") -> dict:
        """
        Register a new user in the system.
    
        Args:
            _id (str): Unique identifier for the user.
            name (str): User's full name.
            email (str): User's email address.
            account_status (str, optional): Account status, defaults to 'active'.
        
        Returns:
            dict: {
                "success": True,
                "message": "User <name> registered."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }
    
        Constraints:
            - _id must be unique among users.
            - name and email must not be empty.
        """
        # Input validation
        if not _id or not name or not email:
            return { "success": False, "error": "Missing required user fields (_id, name, email)." }
        if _id in self.users:
            return { "success": False, "error": f"User with _id '{_id}' already exists." }
    
        # Create user info dict
        user_info: UserInfo = {
            "_id": _id,
            "name": name,
            "email": email,
            "account_status": account_status
        }
        self.users[_id] = user_info
        return { "success": True, "message": f"User {name} registered." }

    def update_user_info(self, user_id: str, updates: dict) -> dict:
        """
        Update specified user information (e.g., email, account_status, name).

        Args:
            user_id (str): The ID of the user to update.
            updates (dict): Dictionary of fields to update. Allowed keys: 'name', 'email', 'account_status'.

        Returns:
            dict: {
                "success": True,
                "message": "User information updated successfully"
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - User must exist.
            - '_id' cannot be changed.
            - Only recognized fields ('name', 'email', 'account_status') can be modified.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        allowed_fields = {'name', 'email', 'account_status'}
        for key in updates:
            if key not in allowed_fields:
                return { "success": False, "error": f"Invalid field '{key}' for user update" }
            # Optionally, enforce type checks (not specified, so omitted).

        # Apply updates
        for key, value in updates.items():
            self.users[user_id][key] = value

        return { "success": True, "message": "User information updated successfully" }


class FitnessChallengeManagementSystem(BaseEnv):
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

    def get_enrollments_by_user_id(self, **kwargs):
        return self._call_inner_tool('get_enrollments_by_user_id', kwargs)

    def get_active_enrollments_by_user_id(self, **kwargs):
        return self._call_inner_tool('get_active_enrollments_by_user_id', kwargs)

    def get_challenge_by_id(self, **kwargs):
        return self._call_inner_tool('get_challenge_by_id', kwargs)

    def get_challenge_details_for_user(self, **kwargs):
        return self._call_inner_tool('get_challenge_details_for_user', kwargs)

    def get_enrollment_status(self, **kwargs):
        return self._call_inner_tool('get_enrollment_status', kwargs)

    def get_enrollment_progress(self, **kwargs):
        return self._call_inner_tool('get_enrollment_progress', kwargs)

    def list_all_challenges(self, **kwargs):
        return self._call_inner_tool('list_all_challenges', kwargs)

    def enroll_user_in_challenge(self, **kwargs):
        return self._call_inner_tool('enroll_user_in_challenge', kwargs)

    def update_enrollment_progress(self, **kwargs):
        return self._call_inner_tool('update_enrollment_progress', kwargs)

    def update_enrollment_status(self, **kwargs):
        return self._call_inner_tool('update_enrollment_status', kwargs)

    def create_challenge(self, **kwargs):
        return self._call_inner_tool('create_challenge', kwargs)

    def update_challenge_status(self, **kwargs):
        return self._call_inner_tool('update_challenge_status', kwargs)

    def edit_challenge_info(self, **kwargs):
        return self._call_inner_tool('edit_challenge_info', kwargs)

    def cancel_enrollment(self, **kwargs):
        return self._call_inner_tool('cancel_enrollment', kwargs)

    def create_user(self, **kwargs):
        return self._call_inner_tool('create_user', kwargs)

    def update_user_info(self, **kwargs):
        return self._call_inner_tool('update_user_info', kwargs)
