# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict



# TypedDicts for each entity

class JobPostInfo(TypedDict):
    job_id: str
    title: str
    description: str
    company_id: str
    location: str
    salary_min: float
    salary_max: float
    date_posted: str
    employment_type: str
    status: str  # (was "sta" in input; expanded here)

class CompanyInfo(TypedDict):
    company_id: str
    name: str
    industry: str
    location: str
    profile: str  # (was "profil" in input; expanded here)

class ApplicationInfo(TypedDict):
    application_id: str
    job_id: str
    seeker_id: str
    application_status: str
    applied_date: str  # (was "applied_da" in input; expanded here)

class JobSeekerInfo(TypedDict):
    seeker_id: str  # (was "ker_id" in input; expanded here)
    name: str
    profile: str
    account_status: str  # (was "account_sta" in input; expanded here)

class _GeneratedEnvImpl:
    def __init__(self):
        # job_posts: {job_id: JobPostInfo}
        self.job_posts: Dict[str, JobPostInfo] = {}
        # companies: {company_id: CompanyInfo}
        self.companies: Dict[str, CompanyInfo] = {}
        # applications: {application_id: ApplicationInfo}
        self.applications: Dict[str, ApplicationInfo] = {}
        # job_seekers: {seeker_id: JobSeekerInfo}
        self.job_seekers: Dict[str, JobSeekerInfo] = {}

        # Constraints:
        # - Job posts must have a defined salary range (salary_min ≤ salary_max).
        # - Only active (status = "open"/"active") job posts are searchable or retrievable via the API.
        # - Each job post must be associated with a valid company.
        # - Applications can only be submitted to job posts that are active.

    def search_job_posts_by_keyword_and_salary(
        self, 
        keyword: str, 
        salary_min: float, 
        salary_max: float
    ) -> dict:
        """
        Search for active job posts where:
          - The title or description contains the keyword (case-insensitive).
          - The job's salary range overlaps with the given [salary_min, salary_max] range.

        Args:
            keyword (str): The keyword to search for (case-insensitive).
            salary_min (float): Minimum salary to filter (inclusive).
            salary_max (float): Maximum salary to filter (inclusive).

        Returns:
            dict:
                On success: {
                    "success": True,
                    "data": List[JobPostInfo]  # May be empty if no matches.
                }
                On failure: {
                    "success": False,
                    "error": str
                }

        Constraints:
            - Only active (status="open" or "active") jobs are included.
            - salary_min must be <= salary_max.
            - Returns job posts where their salary range [job.salary_min, job.salary_max] 
              overlaps with [salary_min, salary_max] (inclusive).
        """
        if salary_min > salary_max:
            return {
                "success": False, 
                "error": "Invalid salary range: salary_min must be less than or equal to salary_max."
            }

        keyword_lower = keyword.lower().strip()
        result = []

        for job in self.job_posts.values():
            # Check active status
            if job["status"].lower() not in {"open", "active"}:
                continue

            # Keyword match in title or description
            title = job["title"].lower()
            description = job["description"].lower()
            if (keyword_lower not in title) and (keyword_lower not in description):
                continue

            # Salary range overlap
            job_min = job["salary_min"]
            job_max = job["salary_max"]
            # Overlap if max(a1, b1) <= min(a2, b2)
            if max(job_min, salary_min) <= min(job_max, salary_max):
                result.append(job)

        return {
            "success": True,
            "data": result
        }

    def search_job_posts_by_criteria(
        self,
        keyword: str = None,
        location: str = None,
        employment_type: str = None,
        company_id: str = None,
        salary_min: float = None,
        salary_max: float = None
    ) -> dict:
        """
        Search active job posts by arbitrary criteria.

        Args:
            keyword (str, optional): Substring (case-insensitive) to match in title or description.
            location (str, optional): Location string (exact match).
            employment_type (str, optional): Employment type string (exact match).
            company_id (str, optional): Company ID (exact match).
            salary_min (float, optional): Require that job's salary_max >= salary_min.
            salary_max (float, optional): Require that job's salary_min <= salary_max.

        Returns:
            dict: {
                "success": True,
                "data": List[JobPostInfo],  # All matching jobs (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Description of the error
            }

        Constraints:
            - Only jobs with status == "open" or "active" are returned.
            - All provided criteria must be satisfied for a job to be included.
        """

        # Parameter validation
        if (salary_min is not None and not isinstance(salary_min, (int, float))) or \
           (salary_max is not None and not isinstance(salary_max, (int, float))):
            return { "success": False, "error": "salary_min and salary_max, if provided, must be numbers" }

        normalized_salary_min = None if salary_min == 0 else salary_min
        normalized_salary_max = None if salary_max == 0 else salary_max
        keyword_lower = keyword.lower() if keyword else None

        matched = []
        for job in self.job_posts.values():
            # Only active job posts
            if job.get("status") not in ("open", "active"):
                continue

            # Keyword match in title or description (if specified)
            if keyword_lower:
                title = job.get("title", "").lower()
                description = job.get("description", "").lower()
                if keyword_lower not in title and keyword_lower not in description:
                    continue

            # Location match (if specified)
            if location and job.get("location") != location:
                continue

            # Employment type match (if specified)
            if employment_type and job.get("employment_type") != employment_type:
                continue

            # Company match (if specified)
            if company_id and job.get("company_id") != company_id:
                continue

            # Salary min/max filtering (if specified)
            if normalized_salary_min is not None and job.get("salary_max") < normalized_salary_min:
                continue
            if normalized_salary_max is not None and job.get("salary_min") > normalized_salary_max:
                continue

            matched.append(job)

        return {"success": True, "data": matched}

    def get_job_post_by_id(self, job_id: str) -> dict:
        """
        Retrieve the full details of a specific job post by its job_id.
    
        Args:
            job_id (str): The unique identifier of the job post.

        Returns:
            dict: If successful:
                      {
                          "success": True,
                          "data": JobPostInfo  # all fields of the job post
                      }
                  If job post not found or not active:
                      {
                          "success": False,
                          "error": <reason>
                      }

        Constraints:
            - Only active job posts (status == "open" or "active") are retrievable via the API.
        """
        job = self.job_posts.get(job_id)
        if not job:
            return { "success": False, "error": "Job post does not exist" }
        if str(job["status"]).lower() not in ("open", "active"):
            return { "success": False, "error": "Job post is not active" }
        return { "success": True, "data": job }

    def list_active_job_posts(self) -> dict:
        """
        List all currently active/open job posts.

        Returns:
            dict: {
                "success": True,
                "data": List[JobPostInfo]  # List of all job posts with status "open" or "active"
            }

        Constraints:
            - Only job posts with status "open" or "active" are included.
            - If no such job posts exist, returns an empty list in 'data'.
        """
        active_job_posts = [
            job_post for job_post in self.job_posts.values()
            if job_post["status"] in ("open", "active")
        ]
        return { "success": True, "data": active_job_posts }

    def get_company_by_id(self, company_id: str) -> dict:
        """
        Retrieve full details of a company by its company_id.

        Args:
            company_id (str): Unique identifier for the company.

        Returns:
            dict: 
                - On success: {"success": True, "data": CompanyInfo}
                - On failure: {"success": False, "error": "Company not found"}
        Constraints:
            - The company must exist in the platform.
        """
        company = self.companies.get(company_id)
        if company is None:
            return {"success": False, "error": "Company not found"}
        return {"success": True, "data": company}

    def get_company_for_job_post(self, job_id: str) -> dict:
        """
        Retrieve the company information associated with a specific (active) job post.

        Args:
            job_id (str): The ID of the job post.

        Returns:
            dict: {
                "success": True,
                "data": CompanyInfo  # Company associated with the job post
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (job post not found, not active, or missing company)
            }

        Constraints:
            - Only active (status="open"/"active") job posts are retrievable.
            - Associated company must exist.
        """
        job_post = self.job_posts.get(job_id)
        if not job_post:
            return { "success": False, "error": "Job post not found" }

        if job_post["status"] not in ("open", "active"):
            return { "success": False, "error": "Job post is not active" }

        company_id = job_post.get("company_id")
        company = self.companies.get(company_id)
        if not company:
            return { "success": False, "error": "Associated company not found" }

        return { "success": True, "data": company }

    def get_applications_for_seeker(self, seeker_id: str) -> dict:
        """
        Retrieve all applications submitted by a specific job seeker.

        Args:
            seeker_id (str): The unique identifier for the job seeker.

        Returns:
            dict: {
                "success": True,
                "data": List[ApplicationInfo]  # all applications by given seeker (may be an empty list)
            }
            or
            {
                "success": False,
                "error": str  # reason for failure (e.g., seeker not found)
            }

        Constraints:
            - seeker_id must exist within self.job_seekers.
        """
        if seeker_id not in self.job_seekers:
            return { "success": False, "error": "Job seeker not found" }

        applications = [app for app in self.applications.values() if app["seeker_id"] == seeker_id]
        return { "success": True, "data": applications }

    def get_applications_for_job_post(self, job_id: str) -> dict:
        """
        List all applications submitted for a given job post.

        Args:
            job_id (str): The unique identifier of the job post.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[ApplicationInfo]  # May be empty if no applications
                    }
                On error (job does not exist):
                    {
                        "success": False,
                        "error": str
                    }
        Constraints:
            - job_id must exist in the current set of job postings.
            - Any applications with the specified job_id should be returned,
              regardless of application_status or job post status.
        """
        if job_id not in self.job_posts:
            return { "success": False, "error": "Job post does not exist" }

        applications = [
            app_info
            for app_info in self.applications.values()
            if app_info["job_id"] == job_id
        ]
        return { "success": True, "data": applications }

    def get_job_seeker_by_id(self, seeker_id: str) -> dict:
        """
        Retrieve information about a job seeker using their seeker_id.

        Args:
            seeker_id (str): The unique identifier of the job seeker.

        Returns:
            dict: 
                On success:
                    {"success": True, "data": JobSeekerInfo}
                On failure:
                    {"success": False, "error": "Job seeker not found"}
        """
        if seeker_id not in self.job_seekers:
            return {"success": False, "error": "Job seeker not found"}
        return {"success": True, "data": self.job_seekers[seeker_id]}

    def validate_job_status_active(self, job_id: str) -> dict:
        """
        Check whether a job post is currently active/open.

        Args:
            job_id (str): The unique identifier of the job post.

        Returns:
            dict:
                {
                    "success": True,
                    "data": bool  # True if job post is active/open, False otherwise
                }
                OR
                {
                    "success": False,
                    "error": "Job post not found"
                }

        Constraints:
            - Only statuses "open" or "active" are considered active.
            - Fails if the job post does not exist.
        """
        job = self.job_posts.get(job_id)
        if not job:
            return {"success": False, "error": "Job post not found"}
        status = job.get("status", "")
        is_active = status.lower() in ("open", "active")
        return {"success": True, "data": is_active}

    def validate_job_salary_range(self, job_id: str) -> dict:
        """
        Check whether the salary range for the specified job post is well-formed (salary_min ≤ salary_max).

        Args:
            job_id (str): The job post ID to validate.

        Returns:
            dict: 
                - If the job exists: { "success": True, "valid": bool }
                - If job_id is invalid: { "success": False, "error": "Job post does not exist" }
        Constraints:
            - The job post must exist.
            - salary_min and salary_max must be compared numerically.
        """
        job = self.job_posts.get(job_id)
        if not job:
            return { "success": False, "error": "Job post does not exist" }
        salary_min = job.get("salary_min")
        salary_max = job.get("salary_max")
        is_valid = salary_min <= salary_max
        return { "success": True, "valid": is_valid }

    def list_all_companies(self) -> dict:
        """
        Retrieve a list of all registered companies on the platform.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[CompanyInfo],  # List of all company info dicts (empty if no companies)
            }

        Constraints:
            - No input parameters.
            - Always succeeds (even if there are no companies).
        """
        companies_list = list(self.companies.values())
        return {
            "success": True,
            "data": companies_list
        }

    def create_job_post(
        self,
        job_id: str,
        title: str,
        description: str,
        company_id: str,
        location: str,
        salary_min: float,
        salary_max: float,
        date_posted: str,
        employment_type: str,
        status: str
    ) -> dict:
        """
        Create a new job post, enforcing company association and salary constraints.

        Args:
            job_id (str): Unique identifier for the job post.
            title (str): Job title.
            description (str): Full job description.
            company_id (str): ID of the associated company (must exist).
            location (str): Location of the job.
            salary_min (float): Minimum salary.
            salary_max (float): Maximum salary.
            date_posted (str): ISO date, or string representation of posting date.
            employment_type (str): Type of employment (e.g., 'full-time').
            status (str): Posting status ('open', 'active', etc).

        Returns:
            dict:
                On success: { "success": True, "message": "Job post created successfully." }
                On failure: { "success": False, "error": <error_message> }

        Constraints:
            - Job post must not duplicate an existing job_id.
            - salary_min ≤ salary_max.
            - company_id must exist in companies.
        """

        # Check unique job_id
        if job_id in self.job_posts:
            return { "success": False, "error": "Job ID already exists." }

        # Company must exist
        if company_id not in self.companies:
            return { "success": False, "error": "Company does not exist." }

        # Salary range is valid
        try:
            salary_min_value = float(salary_min)
            salary_max_value = float(salary_max)
        except Exception:
            return { "success": False, "error": "Salary values must be numbers." }

        if salary_min_value > salary_max_value:
            return { "success": False, "error": "Minimum salary cannot exceed maximum salary." }

        # Create job post
        job_post: JobPostInfo = {
            "job_id": job_id,
            "title": title,
            "description": description,
            "company_id": company_id,
            "location": location,
            "salary_min": salary_min_value,
            "salary_max": salary_max_value,
            "date_posted": date_posted,
            "employment_type": employment_type,
            "status": status
        }
        self.job_posts[job_id] = job_post

        return { "success": True, "message": "Job post created successfully." }

    def update_job_post(self, job_id: str, updates: dict) -> dict:
        """
        Update attributes of an existing job post, ensuring salary range and status validity.

        Args:
            job_id (str): The identifier of the job post to update.
            updates (dict): A dictionary with attribute names and new values to be applied.

        Returns:
            dict: Success or error information:
            - If success: { "success": True, "message": "Job post <job_id> updated successfully" }
            - If error: { "success": False, "error": "<reason>" }

        Constraints:
            - salary_min must be ≤ salary_max if either/both are updated.
            - status can only be updated to allowed values ("open", "active", etc.) if such constraint exists.
            - If company_id is updated, it must refer to an existing company.
            - Only existing job posts can be updated.
        """
        # Check if job exists
        if job_id not in self.job_posts:
            return { "success": False, "error": f"Job post {job_id} does not exist" }

        job_post = self.job_posts[job_id]

        # Prepare for potential salary validation
        salary_min = updates.get("salary_min", job_post["salary_min"])
        salary_max = updates.get("salary_max", job_post["salary_max"])

        if ("salary_min" in updates or "salary_max" in updates):
            # Validate salary constraint
            if not (isinstance(salary_min, (int, float)) and isinstance(salary_max, (int, float))):
                return { "success": False, "error": "salary_min and salary_max must be numbers" }
            if salary_min > salary_max:
                return { "success": False, "error": "salary_min must not exceed salary_max" }

        # Validate company_id if provided
        if "company_id" in updates:
            company_id = updates["company_id"]
            if company_id not in self.companies:
                return { "success": False, "error": f"company_id {company_id} does not exist" }

        # Optionally, you may constrain status to known states
        allowed_statuses = {"open", "active", "closed", "paused", "expired"}
        if "status" in updates:
            status = updates["status"]
            if status not in allowed_statuses:
                return { "success": False, "error": f"Status '{status}' is not permitted" }

        # Apply the updates
        for k, v in updates.items():
            if k in job_post:
                job_post[k] = v

        self.job_posts[job_id] = job_post

        return { "success": True, "message": f"Job post {job_id} updated successfully" }

    def set_job_post_status(self, job_id: str, new_status: str) -> dict:
        """
        Change the status of a job post to the specified value.

        Args:
            job_id (str): Identifier of the job post to be updated.
            new_status (str): The new status to set (e.g., "open", "closed", "inactive").

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "message": "Status of job post <job_id> updated to '<new_status>'."
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason for failure
                    }
        Constraints:
            - The job post with the specified job_id must exist.
            - No restriction on allowed status strings (other than being non-empty).
        """
        if not job_id or not isinstance(job_id, str):
            return { "success": False, "error": "Invalid or missing job_id." }
        if not new_status or not isinstance(new_status, str):
            return { "success": False, "error": "Invalid or missing new_status." }
        if job_id not in self.job_posts:
            return { "success": False, "error": f"Job post with id {job_id} does not exist." }

        self.job_posts[job_id]['status'] = new_status
        return {
            "success": True,
            "message": f"Status of job post {job_id} updated to '{new_status}'."
        }

    def delete_job_post(self, job_id: str) -> dict:
        """
        Remove a job post from the system.

        Args:
            job_id (str): The unique identifier for the job post to be deleted.

        Returns:
            dict:
                - On success: { "success": True, "message": "Job post <job_id> deleted." }
                - On failure: { "success": False, "error": "Job post does not exist." }

        Constraints:
            - Only deletes the job post from system; existing applications pointing to it are not modified.
            - If job_id does not exist, operation fails.
        """
        if job_id not in self.job_posts:
            return { "success": False, "error": "Job post does not exist." }

        del self.job_posts[job_id]
        return { "success": True, "message": f"Job post {job_id} deleted." }

    def create_company(
        self,
        company_id: str,
        name: str,
        industry: str,
        location: str,
        profile: str,
    ) -> dict:
        """
        Add a new company to the platform.

        Args:
            company_id (str): Unique identifier for the company.
            name (str): Company name.
            industry (str): Industry category.
            location (str): Company location.
            profile (str): Company profile/description.

        Returns:
            dict: {
                "success": True,
                "message": "Company created successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - company_id must be unique. If already exists, operation fails.
            - All fields are required and must be non-empty strings.
        """
        # Basic field validation
        if not all(isinstance(field, str) and field.strip() for field in [company_id, name, industry, location, profile]):
            return {"success": False, "error": "All company fields must be non-empty strings."}
        if company_id in self.companies:
            return {"success": False, "error": "A company with this company_id already exists."}

        # Add the new company
        info: CompanyInfo = {
            "company_id": company_id,
            "name": name,
            "industry": industry,
            "location": location,
            "profile": profile,
        }
        self.companies[company_id] = info
        return {"success": True, "message": "Company created successfully."}

    def update_company_info(
        self, 
        company_id: str, 
        name: str = None,
        industry: str = None,
        location: str = None,
        profile: str = None
    ) -> dict:
        """
        Modify information for a company given its company_id. Only non-None values will be updated.

        Args:
            company_id (str): Unique identifier of the company to update.
            name (str, optional): Updated company name.
            industry (str, optional): Updated industry.
            location (str, optional): Updated location.
            profile (str, optional): Updated profile.

        Returns:
            dict: 
                On success: { "success": True, "message": "Company information updated." }
                On failure: { "success": False, "error": "Company not found." }

        Constraints:
            - The company must exist (company_id is valid).
            - Only provided fields are updated; others remain unchanged.
        """
        if company_id not in self.companies:
            return { "success": False, "error": "Company not found." }

        company = self.companies[company_id]
        if name is not None:
            company["name"] = name
        if industry is not None:
            company["industry"] = industry
        if location is not None:
            company["location"] = location
        if profile is not None:
            company["profile"] = profile

        return { "success": True, "message": "Company information updated." }

    @staticmethod
    def _parse_benchmark_datetime(value: str):
        if not isinstance(value, str) or not value.strip():
            return None
        raw = value.strip()
        patterns = [
            ("%Y-%m-%dT%H:%M:%SZ", "datetime"),
            ("%Y-%m-%d %H:%M:%S", "datetime"),
            ("%Y-%m-%d", "date"),
        ]
        for fmt, style in patterns:
            try:
                dt = datetime.strptime(raw, fmt)
                return dt.replace(tzinfo=timezone.utc), style
            except ValueError:
                continue
        return None

    def _infer_application_time_seed(self):
        latest_dt = None
        latest_style = "datetime"

        def _consider(value: str):
            nonlocal latest_dt, latest_style
            parsed = self._parse_benchmark_datetime(value)
            if parsed is None:
                return
            dt, style = parsed
            if latest_dt is None or dt > latest_dt:
                latest_dt = dt
                latest_style = style

        for app in self.applications.values():
            _consider(app.get("applied_date"))
        for job in self.job_posts.values():
            _consider(job.get("date_posted"))

        if latest_dt is None:
            latest_dt = datetime(2023, 1, 1, tzinfo=timezone.utc)
            latest_style = "datetime"

        return latest_dt, latest_style

    def _next_application_timestamp(self):
        if not hasattr(self, "_application_time_cursor"):
            seed_dt, seed_style = self._infer_application_time_seed()
            self._application_time_cursor = seed_dt
            self._application_time_style = seed_style
        style = getattr(self, "_application_time_style", "datetime")
        delta = timedelta(minutes=1) if style == "datetime" else timedelta(days=1)
        self._application_time_cursor = self._application_time_cursor + delta
        ts = self._application_time_cursor
        if style == "date":
            return ts.strftime("%Y-%m-%d"), ts.strftime("%Y%m%d")
        return ts.strftime("%Y-%m-%dT%H:%M:%SZ"), ts.strftime("%Y%m%d%H%M%S")

    def create_job_application(self, job_id: str, seeker_id: str) -> dict:
        """
        Submit a new job application for a given job (if active/open).

        Args:
            job_id (str): The job post ID to apply to.
            seeker_id (str): The job seeker ID submitting the application.

        Returns:
            dict: On success:
                    {
                        "success": True,
                        "message": "Application submitted",
                        "application_id": <new_application_id>
                    }
                  On failure:
                    {
                        "success": False,
                        "error": <reason>
                    }

        Constraints:
            - The job post must exist and have status "open" or "active".
            - The job seeker must exist.
            - The application receives status "submitted" and a benchmark-consistent applied_date.
            - application_id must be unique within the system.
        """

        # Check job post existence and status
        job_post = self.job_posts.get(job_id)
        if not job_post:
            return {"success": False, "error": "Job post does not exist"}
        if job_post["status"] not in ("open", "active"):
            return {"success": False, "error": "Job post is not active"}

        # Check job seeker existence
        if seeker_id not in self.job_seekers:
            return {"success": False, "error": "Job seeker does not exist"}

        applied_date, id_token = self._next_application_timestamp()
        app_base = f"app_{job_id}_{seeker_id}_{id_token}"
        application_id = app_base
        while application_id in self.applications:
            application_id += "_dup"

        # Application info
        application_info = {
            "application_id": application_id,
            "job_id": job_id,
            "seeker_id": seeker_id,
            "application_status": "submitted",
            "applied_date": applied_date
        }

        # Store the application
        self.applications[application_id] = application_info

        return {
            "success": True,
            "message": "Application submitted",
            "application_id": application_id
        }

    def update_application_status(self, application_id: str, new_status: str) -> dict:
        """
        Change the status of an application (e.g., to reviewed, accepted, rejected).

        Args:
            application_id (str): The unique identifier for the application.
            new_status (str): The new status to assign to the application.

        Returns:
            dict: {
                "success": True,
                "message": "Application status updated."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The application_id must exist in the applications database.
            - No check on validity of new_status unless status values are restricted (not specified in environment).
        """
        if application_id not in self.applications:
            return { "success": False, "error": "Application ID does not exist." }
    
        self.applications[application_id]["application_status"] = new_status
        return { "success": True, "message": "Application status updated." }

    def withdraw_job_application(self, application_id: str) -> dict:
        """
        Withdraw (effectively remove) a previously submitted job application.

        Args:
            application_id (str): The ID of the application to withdraw.

        Returns:
            dict: On success:
                      { "success": True, "message": "Application withdrawn." }
                  On failure:
                      { "success": False, "error": <error message> }
        Constraints:
            - Application must exist.
            - Idempotent: If already withdrawn/doesn't exist, error is returned.
        """
        if application_id not in self.applications:
            return { "success": False, "error": "Application does not exist." }
    
        del self.applications[application_id]
        return { "success": True, "message": "Application withdrawn." }

    def create_job_seeker(self, seeker_id: str, name: str, profile: str, account_status: str) -> dict:
        """
        Register a new job seeker account.

        Args:
            seeker_id (str): Unique identifier for the job seeker.
            name (str): Name of the job seeker.
            profile (str): Profile or short description.
            account_status (str): Status of the account (e.g., 'active').

        Returns:
            dict:
                {
                    "success": True,
                    "message": "Job seeker account created."
                }
            or
                {
                    "success": False,
                    "error": <Reason>
                }

        Constraints:
            - seeker_id must be unique.
            - All fields are required and should not be empty.
        """

        # Check for unique seeker_id
        if seeker_id in self.job_seekers:
            return { "success": False, "error": "Job seeker ID already exists." }

        # Check for missing/empty required fields
        if not all([seeker_id, name, profile, account_status]):
            return { "success": False, "error": "Missing required job seeker field(s)." }

        # Optionally validate account_status (e.g., only allow 'active', 'inactive', etc.)
        valid_statuses = {"active", "inactive", "suspended"}
        if account_status not in valid_statuses:
            return { "success": False, "error": "Invalid account status." }

        # Create and add new job seeker
        new_seeker: JobSeekerInfo = {
            "seeker_id": seeker_id,
            "name": name,
            "profile": profile,
            "account_status": account_status
        }
        self.job_seekers[seeker_id] = new_seeker

        return { "success": True, "message": "Job seeker account created." }

    def update_job_seeker_profile(self, seeker_id: str, updates: dict) -> dict:
        """
        Update information and profile details for a job seeker.

        Args:
            seeker_id (str): The ID of the job seeker to update.
            updates (dict): Dictionary of profile fields to update (e.g., {"name": ..., "profile": ...}).

        Returns:
            dict: 
                - { "success": True, "message": "Job seeker profile updated." } on success.
                - { "success": False, "error": "Job seeker not found." } if seeker_id does not exist.
                - { "success": False, "error": "No valid fields to update." } if no updates match.
    
        Constraints:
            - seeker_id must exist.
            - Only valid and allowed fields are updated.
        """
        if seeker_id not in self.job_seekers:
            return { "success": False, "error": "Job seeker not found." }
    
        valid_fields = {"name", "profile", "account_status"}
        job_seeker = self.job_seekers[seeker_id]
        updated = False

        for key, value in updates.items():
            if key in valid_fields:
                job_seeker[key] = value
                updated = True

        if not updated:
            return { "success": False, "error": "No valid fields to update." }
    
        self.job_seekers[seeker_id] = job_seeker
        return { "success": True, "message": "Job seeker profile updated." }

    def set_job_seeker_account_status(self, seeker_id: str, new_status: str) -> dict:
        """
        Change the account status (e.g., active, disabled) of a job seeker.

        Args:
            seeker_id (str): The unique identifier of the job seeker.
            new_status (str): The new account status to set (e.g., 'active', 'disabled').

        Returns:
            dict:
                On success:
                    {"success": True, "message": "Job seeker account status updated."}
                On failure:
                    {"success": False, "error": "<reason>"}

        Constraints:
            - seeker_id must exist in the system.
            - new_status cannot be empty.
        """
        if seeker_id not in self.job_seekers:
            return {"success": False, "error": "Job seeker not found."}
        if not new_status or not new_status.strip():
            return {"success": False, "error": "Account status cannot be empty."}

        # (Optional: Enforce only standard statuses, e.g., "active", "disabled")
        allowed_statuses = {"active", "disabled"}
        if new_status not in allowed_statuses:
            return {"success": False, "error": f"Invalid account status. Allowed: {allowed_statuses}"}

        self.job_seekers[seeker_id]["account_status"] = new_status
        return {"success": True, "message": "Job seeker account status updated."}


class JobBoardPlatform(BaseEnv):
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

    def search_job_posts_by_keyword_and_salary(self, **kwargs):
        return self._call_inner_tool('search_job_posts_by_keyword_and_salary', kwargs)

    def search_job_posts_by_criteria(self, **kwargs):
        return self._call_inner_tool('search_job_posts_by_criteria', kwargs)

    def get_job_post_by_id(self, **kwargs):
        return self._call_inner_tool('get_job_post_by_id', kwargs)

    def list_active_job_posts(self, **kwargs):
        return self._call_inner_tool('list_active_job_posts', kwargs)

    def get_company_by_id(self, **kwargs):
        return self._call_inner_tool('get_company_by_id', kwargs)

    def get_company_for_job_post(self, **kwargs):
        return self._call_inner_tool('get_company_for_job_post', kwargs)

    def get_applications_for_seeker(self, **kwargs):
        return self._call_inner_tool('get_applications_for_seeker', kwargs)

    def get_applications_for_job_post(self, **kwargs):
        return self._call_inner_tool('get_applications_for_job_post', kwargs)

    def get_job_seeker_by_id(self, **kwargs):
        return self._call_inner_tool('get_job_seeker_by_id', kwargs)

    def validate_job_status_active(self, **kwargs):
        return self._call_inner_tool('validate_job_status_active', kwargs)

    def validate_job_salary_range(self, **kwargs):
        return self._call_inner_tool('validate_job_salary_range', kwargs)

    def list_all_companies(self, **kwargs):
        return self._call_inner_tool('list_all_companies', kwargs)

    def create_job_post(self, **kwargs):
        return self._call_inner_tool('create_job_post', kwargs)

    def update_job_post(self, **kwargs):
        return self._call_inner_tool('update_job_post', kwargs)

    def set_job_post_status(self, **kwargs):
        return self._call_inner_tool('set_job_post_status', kwargs)

    def delete_job_post(self, **kwargs):
        return self._call_inner_tool('delete_job_post', kwargs)

    def create_company(self, **kwargs):
        return self._call_inner_tool('create_company', kwargs)

    def update_company_info(self, **kwargs):
        return self._call_inner_tool('update_company_info', kwargs)

    def create_job_application(self, **kwargs):
        return self._call_inner_tool('create_job_application', kwargs)

    def update_application_status(self, **kwargs):
        return self._call_inner_tool('update_application_status', kwargs)

    def withdraw_job_application(self, **kwargs):
        return self._call_inner_tool('withdraw_job_application', kwargs)

    def create_job_seeker(self, **kwargs):
        return self._call_inner_tool('create_job_seeker', kwargs)

    def update_job_seeker_profile(self, **kwargs):
        return self._call_inner_tool('update_job_seeker_profile', kwargs)

    def set_job_seeker_account_status(self, **kwargs):
        return self._call_inner_tool('set_job_seeker_account_status', kwargs)
