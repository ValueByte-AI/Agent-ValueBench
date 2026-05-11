# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
from typing import Optional, List, Dict
import uuid
from datetime import datetime



# Represents a company or organization posting jobs
class EmployerInfo(TypedDict):
    employer_id: str
    name: str
    profile_url: str
    industry: str

# Represents a single job opening including metadata and current status
class JobPostingInfo(TypedDict):
    job_id: str
    employer_id: str
    title: str
    description: str
    location: str
    posting_date: str
    application_link: str
    status: str  # (open, filled, expired, etc.)

# Records state changes of a job posting for auditing and reporting
class JobStatusInfo(TypedDict):
    job_id: str
    status: str  # (open, closed, expired)
    status_update_date: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Online job listing platform state.
        """

        # Employers: {employer_id: EmployerInfo}
        self.employers: Dict[str, EmployerInfo] = {}

        # Job Postings: {job_id: JobPostingInfo}
        self.job_postings: Dict[str, JobPostingInfo] = {}

        # Job Status changes: {job_id: List[JobStatusInfo]}
        self.job_statuses: Dict[str, List[JobStatusInfo]] = {}

        # --- Constraints ---
        # - A job posting must be linked to a valid employer profile
        # - Only jobs with status "open" are considered active openings
        # - Job postings can be searched, filtered, or counted by employer and status

    def get_employer_by_name(self, name: str) -> dict:
        """
        Retrieve detailed employer data by employer name.

        Args:
            name (str): The exact employer name to search for.

        Returns:
            dict:
              On success:
                {
                  "success": True,
                  "data": List[EmployerInfo],  # List of matching employer info dicts
                }
              On failure:
                {
                  "success": False,
                  "error": str  # Reason for failure (e.g., no employer found)
                }

        Constraints:
            - Returns all matching employers with the exact given name.
            - Employer name is not necessarily unique.
        """
        if not isinstance(name, str) or not name.strip():
            return {"success": False, "error": "Invalid or empty employer name"}

        matches = [employer_info for employer_info in self.employers.values() if employer_info["name"] == name]
        if not matches:
            return {"success": False, "error": "No employer found with the given name"}

        return {"success": True, "data": matches}

    def get_employer_by_id(self, employer_id: str) -> dict:
        """
        Retrieve employer profile by employer_id.

        Args:
            employer_id (str): The unique ID of the employer.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": EmployerInfo
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Description of why the lookup failed
                    }

        Constraints:
            - employer_id must exist in the platform's employer database.
        """
        if not employer_id or employer_id not in self.employers:
            return { "success": False, "error": "Employer not found" }

        return { "success": True, "data": self.employers[employer_id] }

    def list_all_employers(self) -> dict:
        """
        List all registered employers (company profiles) on the platform.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[EmployerInfo]  # List may be empty if no employers registered.
            }

        Constraints:
            - No parameters required.
            - Returns all employer entities currently in the platform.
        """
        employers_list = list(self.employers.values())
        return { "success": True, "data": employers_list }

    def list_job_postings_by_employer(self, employer_id: str) -> dict:
        """
        Retrieve all job postings submitted by a particular employer.

        Args:
            employer_id (str): The unique identifier of the employer.

        Returns:
            dict: {
                "success": True,
                "data": List[JobPostingInfo],   # Job postings for this employer (empty list if none)
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g., employer does not exist
            }

        Constraints:
            - The given employer_id must exist in the system.
        """
        if employer_id not in self.employers:
            return { "success": False, "error": "Employer does not exist" }

        results = [
            job_info for job_info in self.job_postings.values()
            if job_info["employer_id"] == employer_id
        ]

        return { "success": True, "data": results }

    def list_job_postings_by_employer_and_status(self, employer_id: str, status: str) -> dict:
        """
        Retrieve all job postings for a specific employer filtered by current status.

        Args:
            employer_id (str): The unique ID of the employer.
            status (str): The desired current status to filter by (e.g., "open", "filled", "expired").

        Returns:
            dict: 
              {
                "success": True,
                "data": List[JobPostingInfo]
              }
              or
              {
                "success": False,
                "error": str
              }

        Constraints:
            - The employer must exist in the platform.
            - Status filtering is applied to the "status" field of job postings.
        """
        if employer_id not in self.employers:
            return {"success": False, "error": "Employer does not exist"}

        data = [
            job_info for job_info in self.job_postings.values()
            if job_info['employer_id'] == employer_id and job_info['status'] == status
        ]

        return {"success": True, "data": data}

    def count_job_postings_by_employer_and_status(self, employer_id: str, status: str) -> dict:
        """
        Count the number of job postings for a specific employer that have a given status.

        Args:
            employer_id (str): Identifier of the employer.
            status (str): The job posting status to count (e.g., "open", "filled", "expired").

        Returns:
            dict: 
                - On success: { "success": True, "data": int }
                - On error: { "success": False, "error": str }

        Constraints:
            - Employer must exist in the platform.
            - Only postings linked to given employer_id are counted.
        """
        if employer_id not in self.employers:
            return {"success": False, "error": "Employer does not exist."}

        count = sum(
            1
            for job in self.job_postings.values()
            if job["employer_id"] == employer_id and job["status"] == status
        )

        return {"success": True, "data": count}

    def get_job_posting_by_id(self, job_id: str) -> dict:
        """
        Retrieve metadata for a specific job posting by its job_id.

        Args:
            job_id (str): The unique identifier of the job posting.

        Returns:
            dict: 
                On success:
                    {
                      "success": True,
                      "data": JobPostingInfo  # Metadata of the job posting
                    }
                On failure:
                    {
                      "success": False,
                      "error": "Job posting not found"
                    }

        Constraints:
            - job_id must exist within self.job_postings.
            - (Indirect) Job postings must be linked to a valid employer at creation but this fetch does not enforce that.
        """
        job = self.job_postings.get(job_id)
        if not job:
            return {"success": False, "error": "Job posting not found"}

        return {"success": True, "data": job}

    def list_job_status_history(self, job_id: str) -> dict:
        """
        Return the full status change history (audit log) for a given job posting.

        Args:
            job_id (str): The unique identifier of the job posting.

        Returns:
            dict: 
                { "success": True, "data": List[JobStatusInfo] } 
                Or { "success": False, "error": <reason> }

        Constraints:
            - The job posting must exist.
            - The result is the (possibly empty) list of status changes for the job posting.
        """
        if job_id not in self.job_postings:
            return { "success": False, "error": "Job posting does not exist" }

        # Get status history; default to empty list if no entries exist
        status_history = self.job_statuses.get(job_id, [])
        return { "success": True, "data": status_history }


    def search_job_postings(
        self, 
        job_id: Optional[str] = None,
        employer_id: Optional[str] = None, 
        status: Optional[str] = None, 
        job_title_keywords: Optional[List[str]] = None, 
        location: Optional[str] = None
    ) -> dict:
        """
        Search for job postings using combined criteria. All parameters are optional.
        The result contains only postings matching all provided filters.

        Args:
            job_id (Optional[str]): Filters to a single job posting by exact job_id. If given, must be a valid job_id.
            employer_id (Optional[str]): Filters jobs by employer. If given, must be a valid employer_id.
            status (Optional[str]): Only jobs matching this status (e.g., 'open', 'filled', etc.).
            job_title_keywords (Optional[List[str]]): List of case-insensitive substrings to match in job title.
            location (Optional[str]): Only jobs with matching location (case insensitive, exact match).

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[JobPostingInfo]
                }
                or
                {
                    "success": False,
                    "error": <reason>
                }

        Constraints:
            - If job_id is provided, it must exist.
            - If employer_id is provided, it must exist.
            - All filters are ANDed. An empty filter returns all postings.
            - job_title_keywords matches if ANY of the provided words is a substring in the title.
            - location match is case-insensitive, full string match.
        """
        if job_id is not None and job_id not in self.job_postings:
            return {"success": False, "error": "Job posting does not exist"}

        # Employer check
        if employer_id is not None and employer_id not in self.employers:
            return {"success": False, "error": "Employer does not exist"}
    
        results = []
        for posting in self.job_postings.values():
            if job_id is not None and posting["job_id"] != job_id:
                continue
            # Employer filter
            if employer_id is not None and posting["employer_id"] != employer_id:
                continue
            # Status filter
            if status is not None and posting.get("status") != status:
                continue
            # Location filter
            if location is not None:
                if not isinstance(posting.get("location"), str):
                    continue
                if posting["location"].lower() != location.lower():
                    continue
            # Job title keywords filter
            if job_title_keywords:
                title = posting.get("title", "")
                if not any(
                    keyword.lower() in title.lower() for keyword in job_title_keywords
                ):
                    continue
            results.append(posting)

        return {"success": True, "data": results}

    def post_new_job(
        self,
        employer_id: str,
        title: str,
        description: str,
        location: str,
        posting_date: str,
        application_link: str
    ) -> dict:
        """
        Create and add a new job posting to the system for a valid employer.
        The job will have status 'open' upon creation, and an initial audit entry is recorded.

        Args:
            employer_id (str): The ID of the employer posting the job. Must be a valid employer.
            title (str): Job title.
            description (str): Job description.
            location (str): Job location.
            posting_date (str): Date of posting (ISO format preferred).
            application_link (str): Link for job applications.

        Returns:
            dict: {
                "success": True,
                "message": "Job posted successfully",
                "job_id": <new_job_id>
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - The employer_id must match an existing employer in the system.
            - job_id is unique and assigned automatically.
        """

        # Check employer exists
        if employer_id not in self.employers:
            return { "success": False, "error": "Employer does not exist" }

        # Generate unique job_id
        while True:
            job_id = str(uuid.uuid4())
            if job_id not in self.job_postings:
                break

        # Compose new JobPostingInfo record
        job_posting = {
            "job_id": job_id,
            "employer_id": employer_id,
            "title": title,
            "description": description,
            "location": location,
            "posting_date": posting_date,
            "application_link": application_link,
            "status": "open"
        }
        self.job_postings[job_id] = job_posting

        # Insert an initial JobStatusInfo audit entry
        status_entry = {
            "job_id": job_id,
            "status": "open",
            "status_update_date": posting_date
        }
        self.job_statuses[job_id] = [status_entry]

        return { "success": True, "message": "Job posted successfully", "job_id": job_id }

    def update_job_status(self, job_id: str, new_status: str, status_update_date: str) -> dict:
        """
        Change the status of a given job posting (e.g., from 'open' to 'filled' or 'expired')
        and record this change in the job's status history.

        Args:
            job_id (str): ID of the job posting to update.
            new_status (str): New status for the job posting (e.g., 'open', 'filled', 'expired').
            status_update_date (str): Date/time of the status update (e.g., ISO format string).

        Returns:
            dict:
                On success:
                    {"success": True, "message": "Job status updated to <new_status> for job <job_id>."}
                On failure:
                    {"success": False, "error": "<reason>"}

        Constraints:
            - The job posting must exist.
            - The status change must be recorded in job_statuses history.
        """
        if job_id not in self.job_postings:
            return {"success": False, "error": "Job posting does not exist."}

        # Update job posting status
        self.job_postings[job_id]['status'] = new_status

        # Append new status history entry
        status_record = {
            "job_id": job_id,
            "status": new_status,
            "status_update_date": status_update_date
        }
        if job_id not in self.job_statuses:
            self.job_statuses[job_id] = []
        self.job_statuses[job_id].append(status_record)

        return {
            "success": True,
            "message": f"Job status updated to {new_status} for job {job_id}."
        }

    def remove_job_posting(self, job_id: str) -> dict:
        """
        Delete a job posting and its status history from the platform.

        Args:
            job_id (str): The unique identifier for the job posting.

        Returns:
            dict:
                - On success:
                    {"success": True, "message": "Job posting removed successfully."}
                - On failure:
                    {"success": False, "error": "Job posting not found."}

        Constraints:
            - The job posting must exist in self.job_postings.
            - Related status change records (if any) are also removed.
        """
        if job_id not in self.job_postings:
            return { "success": False, "error": "Job posting not found." }

        # Remove the job posting
        del self.job_postings[job_id]

        # Remove associated job status history if it exists
        if job_id in self.job_statuses:
            del self.job_statuses[job_id]

        return { "success": True, "message": "Job posting removed successfully." }

    def update_job_posting_metadata(
        self, 
        job_id: str, 
        title: str = None,
        description: str = None,
        location: str = None,
        posting_date: str = None,
        application_link: str = None
    ) -> dict:
        """
        Modify the metadata fields (title, description, location, posting_date, application_link) of an existing job posting.

        Args:
            job_id (str): The ID of the job posting to update.
            title (str, optional): New job title.
            description (str, optional): New job description.
            location (str, optional): New job location.
            posting_date (str, optional): New posting date (ISO string or format as used in state).
            application_link (str, optional): New application link.

        Returns:
            dict:
                - On success: { "success": True, "message": "Job posting metadata updated successfully" }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - job_id must exist.
            - Only attributes title, description, location, posting_date, application_link are updated.
            - Attempting to update job_id or employer_id is ignored (not allowed).
            - If no provided metadata fields to update, operation is a no-op but can be considered successful.
        """
        if job_id not in self.job_postings:
            return { "success": False, "error": "Job posting does not exist" }

        job_post = self.job_postings[job_id]
        updated = False

        if title is not None:
            job_post["title"] = title
            updated = True
        if description is not None:
            job_post["description"] = description
            updated = True
        if location is not None:
            job_post["location"] = location
            updated = True
        if posting_date is not None:
            job_post["posting_date"] = posting_date
            updated = True
        if application_link is not None:
            job_post["application_link"] = application_link
            updated = True

        self.job_postings[job_id] = job_post  # Save changes

        # If nothing was updated, still return success (metadata unchanged)
        return { "success": True, "message": "Job posting metadata updated successfully" }


    def expire_job_postings_by_date(self, cutoff_date: str) -> dict:
        """
        Set status to 'expired' for all job postings whose posting_date is before the provided cutoff_date.
        Also appends a new JobStatusInfo entry for each expired job for auditing.

        Args:
            cutoff_date (str): The cutoff date in ISO format ('YYYY-MM-DD').
    
        Returns:
            dict: 
                - On success: {"success": True, "message": "<N> job postings expired"}
                - On error: {"success": False, "error": "<reason>"}
    
        Constraints:
            - Only jobs not already expired and with posting_date < cutoff_date are updated.
            - posting_date and cutoff_date must be in a valid comparable ISO format.
            - Each status change should be recorded in job_statuses for auditing.
        """
        try:
            cutoff_dt = datetime.strptime(cutoff_date, "%Y-%m-%d").date()
        except Exception:
            return { "success": False, "error": "Invalid cutoff_date format, expected 'YYYY-MM-DD'" }
    
        expired_count = 0
        for job in self.job_postings.values():
            # Parse posting_date
            try:
                posting_dt = datetime.strptime(job["posting_date"], "%Y-%m-%d").date()
            except Exception:
                continue  # Skip unparseable dates
        
            if posting_dt < cutoff_dt and job["status"] != "expired":
                job["status"] = "expired"
                expired_count += 1
                # Log status change in job_statuses
                status_entry = {
                    "job_id": job["job_id"],
                    "status": "expired",
                    "status_update_date": datetime.utcnow().strftime("%Y-%m-%d")
                }
                if job["job_id"] not in self.job_statuses:
                    self.job_statuses[job["job_id"]] = []
                self.job_statuses[job["job_id"]].append(status_entry)

        return { "success": True, "message": f"{expired_count} job postings expired" }

    def reassign_job_posting_employer(self, job_id: str, new_employer_id: str) -> dict:
        """
        Change which employer a job posting is assigned to.

        Args:
            job_id (str): The identifier of the job posting to be reassigned.
            new_employer_id (str): The identifier of the employer to assign the posting to.

        Returns:
            dict: 
                {
                    "success": True,
                    "message": "Job posting {job_id} reassigned to employer {new_employer_id}."
                }
              or
                {
                    "success": False,
                    "error": <error message>
                }

        Constraints:
        - The job_id must identify an existing job posting.
        - The new_employer_id must identify an existing employer.
        """
        if job_id not in self.job_postings:
            return {"success": False, "error": f"Job posting {job_id} does not exist."}

        if new_employer_id not in self.employers:
            return {"success": False, "error": f"Employer {new_employer_id} does not exist."}

        # Reassign the job posting to the new employer
        self.job_postings[job_id]['employer_id'] = new_employer_id

        return {
            "success": True,
            "message": f"Job posting {job_id} reassigned to employer {new_employer_id}."
        }


class OnlineJobListingPlatform(BaseEnv):
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

    def get_employer_by_name(self, **kwargs):
        return self._call_inner_tool('get_employer_by_name', kwargs)

    def get_employer_by_id(self, **kwargs):
        return self._call_inner_tool('get_employer_by_id', kwargs)

    def list_all_employers(self, **kwargs):
        return self._call_inner_tool('list_all_employers', kwargs)

    def list_job_postings_by_employer(self, **kwargs):
        return self._call_inner_tool('list_job_postings_by_employer', kwargs)

    def list_job_postings_by_employer_and_status(self, **kwargs):
        return self._call_inner_tool('list_job_postings_by_employer_and_status', kwargs)

    def count_job_postings_by_employer_and_status(self, **kwargs):
        return self._call_inner_tool('count_job_postings_by_employer_and_status', kwargs)

    def get_job_posting_by_id(self, **kwargs):
        return self._call_inner_tool('get_job_posting_by_id', kwargs)

    def list_job_status_history(self, **kwargs):
        return self._call_inner_tool('list_job_status_history', kwargs)

    def search_job_postings(self, **kwargs):
        return self._call_inner_tool('search_job_postings', kwargs)

    def post_new_job(self, **kwargs):
        return self._call_inner_tool('post_new_job', kwargs)

    def update_job_status(self, **kwargs):
        return self._call_inner_tool('update_job_status', kwargs)

    def remove_job_posting(self, **kwargs):
        return self._call_inner_tool('remove_job_posting', kwargs)

    def update_job_posting_metadata(self, **kwargs):
        return self._call_inner_tool('update_job_posting_metadata', kwargs)

    def expire_job_postings_by_date(self, **kwargs):
        return self._call_inner_tool('expire_job_postings_by_date', kwargs)

    def reassign_job_posting_employer(self, **kwargs):
        return self._call_inner_tool('reassign_job_posting_employer', kwargs)
