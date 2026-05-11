# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Any
import uuid
import datetime
from typing import Dict, Any
from datetime import datetime



class JobPostingInfo(TypedDict):
    job_id: str
    title: str
    description: str
    industry: str
    location: str
    employer_id: str
    date_posted: str
    status: str  # e.g., 'open', 'closed'

class EmployerInfo(TypedDict):
    employer_id: str
    name: str
    organization_detail: str

class JobSeekerInfo(TypedDict):
    job_seeker_id: str
    name: str
    preferences: Dict[str, Any]
    profile_detail: str

class JobApplicationInfo(TypedDict):
    application_id: str
    job_id: str
    job_seeker_id: str
    status: str  # e.g., 'applied', 'reviewed', 'interview', 'rejected', etc.
    date_applied: str

class MessageInfo(TypedDict):
    message_id: str
    sender_id: str
    receiver_id: str
    timestamp: str
    content: str
    related_job_id: str

class SearchSessionInfo(TypedDict):
    session_id: str
    job_seeker_id: str
    criteria: Dict[str, Any]
    page_number: int
    page_size: int
    timestamp: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Job Postings: {job_id: JobPostingInfo}
        self.job_postings: Dict[str, JobPostingInfo] = {}

        # Employers: {employer_id: EmployerInfo}
        self.employers: Dict[str, EmployerInfo] = {}

        # Job Seekers: {job_seeker_id: JobSeekerInfo}
        self.job_seekers: Dict[str, JobSeekerInfo] = {}

        # Job Applications: {application_id: JobApplicationInfo}
        self.job_applications: Dict[str, JobApplicationInfo] = {}

        # Messages: {message_id: MessageInfo}
        self.messages: Dict[str, MessageInfo] = {}

        # Search Sessions: {session_id: SearchSessionInfo}
        self.search_sessions: Dict[str, SearchSessionInfo] = {}

        # --- Constraints (annotated for later enforcement) ---
        # - Only active (status = 'open') job postings are shown to job seekers.
        # - Pagination limits number of results per page (e.g., 15 max).
        # - Employers can only manage their own job postings.
        # - Job seekers can only apply to open postings.
        # - Messaging is only allowed between employers and applicants, for specific jobs.
        # - All jobs must have a valid industry and location assigned.

    def search_job_postings_by_criteria(
        self,
        criteria: Dict[str, Any],
        page_number: int,
        page_size: int
    ) -> dict:
        """
        Filter and retrieve job postings based on given criteria (e.g., industry, location, etc.), with pagination.
        Only active (status='open') job postings are returned.

        Args:
            criteria (Dict[str, Any]): Filtering fields and desired values, e.g. {'industry': 'IT', 'location': 'NY'}
            page_number (int): 1-based page index (>=1)
            page_size (int): Items per page (max 15; if higher, will be capped to 15).

        Returns:
            dict: {
                "success": True,
                "data": List[JobPostingInfo],  # List of job postings on this page
                "total_results": int,          # Total count of results matching criteria
                "page_number": int, 
                "page_size": int
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Only open job postings are shown (status='open').
            - Pagination page_size capped to 15.
            - Invalid values for page_number (<1) or page_size (<1) give error.
        """

        MAX_PAGE_SIZE = 15
        if not isinstance(page_number, int) or page_number < 1:
            return {"success": False, "error": "Invalid page_number: must be >= 1."}
        if not isinstance(page_size, int) or page_size < 1:
            return {"success": False, "error": "Invalid page_size: must be >= 1."}
    
        page_size = min(page_size, MAX_PAGE_SIZE)

        # Only consider open jobs
        postings = [jp for jp in self.job_postings.values() if jp.get("status") == "open"]

        # Apply each criterion (all must match)
        for key, val in (criteria or {}).items():
            # Filter (Note: robust even if key is not present in all postings)
            postings = [jp for jp in postings if key in jp and jp[key] == val]

        total_results = len(postings)
        # Pagination math (1-based page_number)
        start_idx = (page_number - 1) * page_size
        end_idx = start_idx + page_size
        paged_results = postings[start_idx:end_idx]

        # If page out of range, paged_results=empty (acceptable)
        return {
            "success": True,
            "data": paged_results,
            "total_results": total_results,
            "page_number": page_number,
            "page_size": page_size
        }

    def get_job_posting_by_id(self, job_id: str) -> dict:
        """
        Retrieve full details for a specific job posting by its unique ID.

        Args:
            job_id (str): The unique identifier for the job posting.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": JobPostingInfo
                    }
                On error:
                    {
                        "success": False,
                        "error": str  # "Job posting not found"
                    }

        Constraints:
            - job_id must exist in self.job_postings.
        """
        posting = self.job_postings.get(job_id)
        if posting is None:
            return {"success": False, "error": "Job posting not found"}
        return {"success": True, "data": posting}

    def list_job_postings_by_employer(self, employer_id: str) -> dict:
        """
        Retrieve all job postings posted by a specific employer.

        Args:
            employer_id (str): The unique identifier of the employer.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": List[JobPostingInfo],  # All postings by this employer (may be empty)
                }
                or
                {
                    "success": False,
                    "error": str  # Reason if employer does not exist
                }

        Constraints:
            - The employer must exist.
            - Returns all postings, regardless of status ('open', 'closed', etc.).
        """
        if employer_id not in self.employers:
            return {"success": False, "error": "Employer does not exist."}

        postings = [
            posting for posting in self.job_postings.values()
            if posting["employer_id"] == employer_id
        ]
        return {"success": True, "data": postings}

    def get_employer_by_id(self, employer_id: str) -> dict:
        """
        Retrieve profile and organizational details for a given employer by employer_id.

        Args:
            employer_id (str): The unique identifier for the employer.

        Returns:
            dict: {
                "success": True,
                "data": EmployerInfo
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - employer_id must exist in the portal system.
        """
        employer = self.employers.get(employer_id)
        if employer is None:
            return {"success": False, "error": "Employer not found"}
        return {"success": True, "data": employer}

    def get_job_seeker_by_id(self, job_seeker_id: str) -> dict:
        """
        Retrieve the complete profile and preferences for the given job seeker.

        Args:
            job_seeker_id (str): The unique identifier of the job seeker.

        Returns:
            dict:
                success: True and data (JobSeekerInfo) if the job seeker exists,
                         False and error message otherwise.

        Constraints:
            - job_seeker_id must refer to an existing job seeker.
            - No permission checks, pure lookup.

        Example success:
            {"success": True, "data": {...job seeker info...}}

        Example failure:
            {"success": False, "error": "Job seeker not found"}
        """
        info = self.job_seekers.get(job_seeker_id)
        if info is None:
            return {"success": False, "error": "Job seeker not found"}
        return {"success": True, "data": info}

    def get_job_applications_by_job_seeker(self, job_seeker_id: str) -> dict:
        """
        List all job applications submitted by the specified job seeker.

        Args:
            job_seeker_id (str): The job seeker whose applications are to be listed.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[JobApplicationInfo]  # List of the job seeker's applications (possibly empty)
                }
                or
                {
                    "success": False,
                    "error": str  # Error message (e.g., job seeker not found)
                }

        Constraints:
            - The provided job_seeker_id must exist in the system.
        """
        if job_seeker_id not in self.job_seekers:
            return { "success": False, "error": "Job seeker not found" }

        applications = [
            app for app in self.job_applications.values()
            if app["job_seeker_id"] == job_seeker_id
        ]

        return { "success": True, "data": applications }

    def get_job_applications_by_job_id(self, job_id: str) -> dict:
        """
        Show all job applications submitted for a specific job.

        Args:
            job_id (str): The ID of the job posting.

        Returns:
            dict: 
                If job exists:
                    {
                        "success": True,
                        "data": List[JobApplicationInfo]  # May be empty if no applications
                    }
                If job does not exist:
                    {
                        "success": False,
                        "error": "Job posting does not exist."
                    }
        Constraints:
            - job_id must exist in job_postings.
            - No restriction on viewing applications (all applications returned for job_id).
        """
        if job_id not in self.job_postings:
            return { "success": False, "error": "Job posting does not exist." }

        apps = [
            app_info for app_info in self.job_applications.values()
            if app_info["job_id"] == job_id
        ]

        return { "success": True, "data": apps }

    def list_messages_by_job_and_user(self, job_id: str, employer_id: str, job_seeker_id: str) -> dict:
        """
        Retrieve all conversation/messages related to a specific job posting between the employer and a particular job seeker.

        Args:
            job_id (str): The job posting's unique ID.
            employer_id (str): The employer's user ID (must match job's employer).
            job_seeker_id (str): The job seeker's user ID.

        Returns:
            dict:
                - success: True, data: List[MessageInfo] if query successful (list may be empty if no messages)
                - success: False, error: str if any entity does not exist, or employer-job linkage is invalid

        Constraints:
            - Job must exist.
            - Employer must exist and own the job (job_postings[job_id]['employer_id'] == employer_id).
            - Job seeker must exist.
            - Only messages where related_job_id==job_id and sender/receiver is employer_id/job_seeker_id (in both directions).
        """
        # Check existence of job
        job = self.job_postings.get(job_id)
        if not job:
            return {"success": False, "error": "Job posting does not exist"}

        # Check employer exists
        employer = self.employers.get(employer_id)
        if not employer:
            return {"success": False, "error": "Employer does not exist"}

        # Check job_seeker exists
        job_seeker = self.job_seekers.get(job_seeker_id)
        if not job_seeker:
            return {"success": False, "error": "Job seeker does not exist"}

        # Employer must own the job posting
        if job['employer_id'] != employer_id:
            return {"success": False, "error": "Employer does not own this job posting"}

        # Find relevant messages
        messages = []
        for msg in self.messages.values():
            if (
                msg['related_job_id'] == job_id and
                (
                    (msg['sender_id'] == employer_id and msg['receiver_id'] == job_seeker_id) or
                    (msg['sender_id'] == job_seeker_id and msg['receiver_id'] == employer_id)
                )
            ):
                messages.append(msg)

        return {"success": True, "data": messages}

    def get_search_session(self, session_id: str = None, job_seeker_id: str = None) -> dict:
        """
        Retrieve the saved search session (search criteria, page context) for a job seeker by session_id or job_seeker_id.

        Args:
            session_id (str, optional): Specific session ID to retrieve.
            job_seeker_id (str, optional): Find latest search session for this job seeker if session_id is not provided.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": SearchSessionInfo
                    }
                On failure:
                    {
                        "success": False,
                        "error": str
                    }
        Constraints:
            - At least one parameter (session_id or job_seeker_id) must be provided.
            - If session_id is given but not found, returns error.
            - If job_seeker_id is given but no sessions found, returns error.
            - If both given, session_id takes precedence.
        """
        # Priority: session_id > job_seeker_id
        if session_id:
            session = self.search_sessions.get(session_id)
            if not session:
                return {"success": False, "error": "Session with session_id not found"}
            return {"success": True, "data": session}
        elif job_seeker_id:
            # Find all sessions for this job seeker
            matching_sessions = [
                session for session in self.search_sessions.values()
                if session["job_seeker_id"] == job_seeker_id
            ]
            if not matching_sessions:
                return {"success": False, "error": "No search session found for given job_seeker_id"}
            # Return the latest session (by timestamp, assuming ISO string order is valid)
            latest_session = max(matching_sessions, key=lambda s: s["timestamp"])
            return {"success": True, "data": latest_session}
        else:
            return {"success": False, "error": "Must provide session_id or job_seeker_id"}


    def create_search_session(
        self,
        job_seeker_id: str,
        criteria: Dict[str, Any],
        page_number: int,
        page_size: int
    ) -> dict:
        """
        Create and store a new search session for a job seeker.

        Args:
            job_seeker_id (str): The job seeker for whom the session is being created.
            criteria (dict): Search criteria (e.g., fields for job filtering).
            page_number (int): Page number (must be >0; defaults to 1 if invalid).
            page_size (int): Number of results per page (maximum 15).

        Returns:
            dict: On success:
                {
                    "success": True,
                    "message": "Search session created",
                    "session_id": <session_id>,
                    "session": <session_dict>
                }
            On failure:
                {
                    "success": False,
                    "error": <reason>
                }

        Constraints:
            - Page size is capped at 15 results.
            - Must be associated with an existing job seeker.
        """
        # Check job seeker existence
        if job_seeker_id not in self.job_seekers:
            return { "success": False, "error": "Job seeker does not exist" }

        # Sanitize page number and page size
        if not isinstance(page_number, int) or page_number < 1:
            page_number = 1
        if not isinstance(page_size, int) or page_size < 1:
            page_size = 1
        if page_size > 15:
            page_size = 15

        # Generate unique session_id
        session_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        session = {
            "session_id": session_id,
            "job_seeker_id": job_seeker_id,
            "criteria": criteria,
            "page_number": page_number,
            "page_size": page_size,
            "timestamp": timestamp
        }

        self.search_sessions[session_id] = session

        return {
            "success": True,
            "message": "Search session created",
            "session_id": session_id,
            "session": session
        }

    def update_search_session(
        self,
        session_id: str,
        criteria: dict = None,
        page_number: int = None,
        page_size: int = None,
        timestamp: str = None
    ) -> dict:
        """
        Update fields (criteria, page_number, page_size, timestamp) of an existing search session.

        Args:
            session_id (str): ID of the session to update.
            criteria (dict, optional): Updated search/filter criteria for the session.
            page_number (int, optional): The page number to set in the session.
            page_size (int, optional): The page size (max results per page), maximum allowed is 15.
            timestamp (str, optional): Last updated timestamp or session time.

        Returns:
            dict:
                Success: { "success": True, "message": "Search session updated" }
                Failure: { "success": False, "error": <reason> }

        Constraints:
            - Page size must not exceed 15; if it does, it is set to 15.
            - session_id must exist.
            - Only provided fields are updated.
        """
        if session_id not in self.search_sessions:
            return { "success": False, "error": "No such search session" }

        session = self.search_sessions[session_id]

        if criteria is not None:
            session["criteria"] = criteria
        if page_number is not None:
            session["page_number"] = page_number
        if page_size is not None:
            session["page_size"] = min(page_size, 15)
        if timestamp is not None:
            session["timestamp"] = timestamp

        self.search_sessions[session_id] = session

        return { "success": True, "message": "Search session updated" }

    def apply_to_job_posting(self, job_seeker_id: str, job_id: str) -> dict:
        """
        Create a new job application for a job seeker for a specified open job posting.

        Args:
            job_seeker_id (str): ID of the job seeker applying.
            job_id (str): ID of the job posting to apply for.

        Returns:
            dict: {
                "success": True,
                "message": "Application submitted successfully."
            }
            or
            {
                "success": False,
                "error": <error message>
            }

        Constraints:
            - Job seeker and job posting must exist.
            - Job posting must be open (status == 'open').
            - Job seeker can only apply once to a specific job.
        """

        # Check if job seeker exists
        if job_seeker_id not in self.job_seekers:
            return {"success": False, "error": "Job seeker does not exist."}

        # Check if job posting exists
        if job_id not in self.job_postings:
            return {"success": False, "error": "Job posting does not exist."}

        job = self.job_postings[job_id]

        # Check job posting status
        if job.get("status") != "open":
            return {"success": False, "error": "Job posting is not open for applications."}

        # Check if already applied
        for app in self.job_applications.values():
            if app["job_id"] == job_id and app["job_seeker_id"] == job_seeker_id:
                return {"success": False, "error": "Job seeker has already applied to this job."}

        # Create new application
        application_id = str(uuid.uuid4())
        date_applied = datetime.now().isoformat()

        new_app = {
            "application_id": application_id,
            "job_id": job_id,
            "job_seeker_id": job_seeker_id,
            "status": "applied",
            "date_applied": date_applied
        }

        self.job_applications[application_id] = new_app

        return {
            "success": True,
            "message": "Application submitted successfully."
        }

    def send_message(
        self,
        sender_id: str,
        receiver_id: str,
        related_job_id: str,
        content: str,
        timestamp: str
    ) -> dict:
        """
        Send a message between employer and job seeker regarding a specific job posting.

        Args:
            sender_id (str): User ID of the sender (must be employer or job seeker).
            receiver_id (str): User ID of the receiver (must be job seeker or employer, respectively).
            related_job_id (str): The job posting associated with the message.
            content (str): Content of the message (non-empty).
            timestamp (str): Timestamp for the message.

        Returns:
            dict: Success or failure message.

        Constraints:
            - Messaging is only permitted between an employer and an applicant (job seeker) regarding a job.
            - The job must exist.
            - The job seeker must have applied for the specified job.
            - Either sender or receiver must be an employer, and the other a job seeker (not both employers or both job seekers).
            - The message must have non-empty content.
        """
        # Validate job posting exists
        job = self.job_postings.get(related_job_id)
        if not job:
            return {"success": False, "error": "Job posting does not exist."}

        # Identify sender and receiver types
        sender_is_employer = sender_id in self.employers
        receiver_is_employer = receiver_id in self.employers
        sender_is_job_seeker = sender_id in self.job_seekers
        receiver_is_job_seeker = receiver_id in self.job_seekers

        # Must be employer <-> job seeker pair
        if (sender_is_employer and receiver_is_employer) or (sender_is_job_seeker and receiver_is_job_seeker):
            return {"success": False, "error": "Messaging is only permitted between an employer and a job seeker."}
        if not (
            (sender_is_employer and receiver_is_job_seeker) or
            (sender_is_job_seeker and receiver_is_employer)
        ):
            return {"success": False, "error": "Sender or receiver does not exist or has invalid roles."}

        # Identify which one is the job seeker
        if sender_is_job_seeker:
            job_seeker_id = sender_id
        else:
            job_seeker_id = receiver_id

        # Verify the job seeker has actually applied to the job
        found_application = False
        for app in self.job_applications.values():
            if app["job_id"] == related_job_id and app["job_seeker_id"] == job_seeker_id:
                found_application = True
                break
        if not found_application:
            return {
                "success": False,
                "error": "The job seeker has not applied to this job. Messaging not permitted."
            }

        # Message content must not be empty
        if not content.strip():
            return {"success": False, "error": "Message content cannot be empty."}

        # All constraints satisfied, create message
        message_id = f"msg_{len(self.messages)+1:06d}"
        message = {
            "message_id": message_id,
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "timestamp": timestamp,
            "content": content,
            "related_job_id": related_job_id,
        }
        self.messages[message_id] = message
        return {"success": True, "message": "Message sent successfully."}

    def edit_job_posting(
        self,
        job_id: str,
        employer_id: str,
        updates: dict
    ) -> dict:
        """
        Update the details of a job posting.
        Only the employer who owns the posting may perform this operation.
        Certain fields ('industry' and 'location') must not be empty post-update.

        Args:
            job_id (str): The job posting to update.
            employer_id (str): The employer attempting the edit.
            updates (dict): Fields to update (title, description, industry, location, status).

        Returns:
            dict:
                - On success: { "success": True, "message": "Job posting updated successfully." }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - Only the posting's owner (by employer_id) may edit.
            - Job must always have a valid, non-empty industry and location.
            - 'job_id' and 'employer_id' cannot be updated.
        """
        # Check job exists
        posting = self.job_postings.get(job_id)
        if not posting:
            return {"success": False, "error": "Job posting not found."}

        # Check permission
        if posting["employer_id"] != employer_id:
            return {"success": False, "error": "Permission denied: cannot edit others' postings."}

        # Determine allowed updatable fields
        allowed_fields = {"title", "description", "industry", "location", "status"}
        update_fields = {k: v for k, v in updates.items() if k in allowed_fields}
        if not update_fields:
            return {"success": False, "error": "No valid fields provided for update."}

        # Stage update
        new_posting = dict(posting)
        new_posting.update(update_fields)

        # Validate industry and location
        if not new_posting.get("industry") or not isinstance(new_posting["industry"], str) or not new_posting["industry"].strip():
            return {"success": False, "error": "Industry must be a non-empty string."}
        if not new_posting.get("location") or not isinstance(new_posting["location"], str) or not new_posting["location"].strip():
            return {"success": False, "error": "Location must be a non-empty string."}

        # Do update
        posting.update(update_fields)
        return {"success": True, "message": "Job posting updated successfully."}

    def delete_job_posting(self, job_id: str, employer_id: str) -> dict:
        """
        Remove an existing job posting.
    
        Only the employer who owns (created) the posting may delete it.
    
        Args:
            job_id (str): The ID of the job posting to be deleted.
            employer_id (str): The employer attempting the deletion.

        Returns:
            dict: {
                "success": True,
                "message": str  # Success confirmation message.
            }
            OR
            {
                "success": False,
                "error": str  # Error description.
            }

        Constraints:
            - Job posting must exist.
            - Employer must exist.
            - Employer must own the job posting (only owners can delete).
        """
        # Validate job posting existence
        job = self.job_postings.get(job_id)
        if not job:
            return { "success": False, "error": "Job posting does not exist." }
    
        # Validate employer existence
        employer = self.employers.get(employer_id)
        if not employer:
            return { "success": False, "error": "Employer not found." }

        # Ownership check
        if job["employer_id"] != employer_id:
            return { "success": False, "error": "Permission denied: Employer does not own this job posting." }
    
        # Delete job posting
        del self.job_postings[job_id]
    
        return {
            "success": True,
            "message": f"Job posting {job_id} has been deleted."
        }


    def create_job_posting(
        self,
        employer_id: str,
        title: str,
        description: str,
        industry: str,
        location: str
    ) -> dict:
        """
        Allow an employer to create/post a new job vacancy.
    
        Args:
            employer_id (str): The employer's unique identifier.
            title (str): The job title.
            description (str): Description of the job.
            industry (str): The industry (must be non-empty).
            location (str): Job location (must be non-empty).

        Returns:
            dict: 
              On success: { "success": True, "message": "Job posting created", "job_id": <generated_job_id> }
              On failure: { "success": False, "error": "reason" }

        Constraints:
            - All input fields are required and must not be empty.
            - Only registered employers may create postings.
            - Job posting gets a unique ID, 'open' status, and current date_posted.
            - Job industry and location must be provided.
        """
        # Validate employer exists
        if not employer_id or employer_id not in self.employers:
            return { "success": False, "error": "Invalid or unknown employer_id" }
    
        # Check required fields
        missing_fields = []
        if not title: missing_fields.append("title")
        if not description: missing_fields.append("description")
        if not industry: missing_fields.append("industry")
        if not location: missing_fields.append("location")
        if missing_fields:
            return { "success": False, "error": f"Missing required fields: {', '.join(missing_fields)}" }
    
        # Generate unique job_id
        job_id = str(uuid.uuid4())
        while job_id in self.job_postings:
            job_id = str(uuid.uuid4())

        date_posted = datetime.now().isoformat()

        new_job = {
            "job_id": job_id,
            "title": title,
            "description": description,
            "industry": industry,
            "location": location,
            "employer_id": employer_id,
            "date_posted": date_posted,
            "status": "open"
        }
        self.job_postings[job_id] = new_job

        return {
            "success": True,
            "message": "Job posting created",
            "job_id": job_id
        }

    def update_job_application_status(self, application_id: str, new_status: str) -> dict:
        """
        Change the status of a job application (e.g., to 'reviewed', 'interview', 'rejected', etc.).

        Args:
            application_id (str): The unique ID of the job application to update.
            new_status (str): The new status to be set for the application.

        Returns:
            dict:
                - On success: { "success": True, "message": "Job application status updated." }
                - On error: { "success": False, "error": "reason" }

        Constraints:
            - The job application with 'application_id' must exist.
            - No restrictions on new_status. (Assumed from spec.)
        """
        app = self.job_applications.get(application_id)
        if not app:
            return { "success": False, "error": "Job application does not exist." }

        app["status"] = new_status
        # No timestamps required on update per JobApplicationInfo schema.
        return { "success": True, "message": "Job application status updated." }

    def update_job_seeker_profile(self, job_seeker_id: str, new_data: dict) -> dict:
        """
        Edit a job seeker's profile information or preferences.

        Args:
            job_seeker_id (str): ID of the job seeker whose profile to update.
            new_data (dict): Dictionary containing updated values for keys:
                - 'name' (str, optional)
                - 'preferences' (dict, optional)
                - 'profile_detail' (str, optional)

        Returns:
            dict: {
                "success": True,
                "message": "Job seeker profile updated successfully."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }
    
        Constraints:
            - job_seeker_id must exist.
            - Only 'name', 'preferences', 'profile_detail' are updatable.
            - 'preferences' must remain a dict if provided.
        """
        allowed_fields = {"name", "preferences", "profile_detail"}
        if job_seeker_id not in self.job_seekers:
            return { "success": False, "error": "Job seeker not found." }
        if not isinstance(new_data, dict) or not new_data:
            return { "success": False, "error": "No update data provided." }

        valid_update = False
        job_seeker = self.job_seekers[job_seeker_id]
        for key, value in new_data.items():
            if key not in allowed_fields:
                continue  # ignore invalid fields
            if key == "preferences" and not isinstance(value, dict):
                return { "success": False, "error": "'preferences' field must be a dictionary." }
            job_seeker[key] = value
            valid_update = True

        if not valid_update:
            return { "success": False, "error": "No valid updatable fields provided." }

        return { "success": True, "message": "Job seeker profile updated successfully." }


class OnlineJobPortalSystem(BaseEnv):
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

    def search_job_postings_by_criteria(self, **kwargs):
        return self._call_inner_tool('search_job_postings_by_criteria', kwargs)

    def get_job_posting_by_id(self, **kwargs):
        return self._call_inner_tool('get_job_posting_by_id', kwargs)

    def list_job_postings_by_employer(self, **kwargs):
        return self._call_inner_tool('list_job_postings_by_employer', kwargs)

    def get_employer_by_id(self, **kwargs):
        return self._call_inner_tool('get_employer_by_id', kwargs)

    def get_job_seeker_by_id(self, **kwargs):
        return self._call_inner_tool('get_job_seeker_by_id', kwargs)

    def get_job_applications_by_job_seeker(self, **kwargs):
        return self._call_inner_tool('get_job_applications_by_job_seeker', kwargs)

    def get_job_applications_by_job_id(self, **kwargs):
        return self._call_inner_tool('get_job_applications_by_job_id', kwargs)

    def list_messages_by_job_and_user(self, **kwargs):
        return self._call_inner_tool('list_messages_by_job_and_user', kwargs)

    def get_search_session(self, **kwargs):
        return self._call_inner_tool('get_search_session', kwargs)

    def create_search_session(self, **kwargs):
        return self._call_inner_tool('create_search_session', kwargs)

    def update_search_session(self, **kwargs):
        return self._call_inner_tool('update_search_session', kwargs)

    def apply_to_job_posting(self, **kwargs):
        return self._call_inner_tool('apply_to_job_posting', kwargs)

    def send_message(self, **kwargs):
        return self._call_inner_tool('send_message', kwargs)

    def edit_job_posting(self, **kwargs):
        return self._call_inner_tool('edit_job_posting', kwargs)

    def delete_job_posting(self, **kwargs):
        return self._call_inner_tool('delete_job_posting', kwargs)

    def create_job_posting(self, **kwargs):
        return self._call_inner_tool('create_job_posting', kwargs)

    def update_job_application_status(self, **kwargs):
        return self._call_inner_tool('update_job_application_status', kwargs)

    def update_job_seeker_profile(self, **kwargs):
        return self._call_inner_tool('update_job_seeker_profile', kwargs)
