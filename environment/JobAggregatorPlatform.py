# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Any
import re
import time



class JobPostingInfo(TypedDict):
    job_id: str
    title: str
    company: str
    location: str
    description: str
    source_id: str
    date_posted: str
    employment_type: str
    salary_range: str
    url: str
    status: str  # active/expired/etc.

class DataSourceInfo(TypedDict):
    source_id: str
    name: str
    api_type: str
    last_synced: str
    reliability_rating: float

class SearchQueryInfo(TypedDict):
    query_id: str
    user_id: str
    keywords: List[str]
    location: str
    date_created: str
    filters: Dict[str, Any]

class UserInfo(TypedDict):
    user_id: str
    preferences: Dict[str, Any]
    search_history: List[str]  # list of query_ids
    comparison_history: List[str]  # list of job_id pairs, job_ids, etc.

class _GeneratedEnvImpl:
    def __init__(self):
        # JobPostings: {job_id: JobPostingInfo}
        self.job_postings: Dict[str, JobPostingInfo] = {}

        # DataSources: {source_id: DataSourceInfo}
        self.data_sources: Dict[str, DataSourceInfo] = {}

        # SearchQueries: {query_id: SearchQueryInfo}
        self.search_queries: Dict[str, SearchQueryInfo] = {}

        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # --- Constraints (see below) ---
        # - Each job posting is uniquely associated with a source_id.
        # - Job postings may be duplicated across data sources but should be distinguishable.
        # - Search queries only return jobs matching specified filters (e.g., location, keywords).
        # - Only active (non-expired) job postings are displayed to users.
        # - User preferences and search histories are stored for personalization/comparison.

    def list_data_sources(self) -> dict:
        """
        Retrieve information on all job data providers (API type, reliability, etc.).

        Returns:
            dict: {
                "success": True,
                "data": List[DataSourceInfo]  # List (may be empty) of all DataSourceInfo dictionaries
            }
        Constraints:
            - No input parameters.
            - Returns all data sources even if empty (as empty list).
        """
        data_sources_list = list(self.data_sources.values())
        return { "success": True, "data": data_sources_list }

    def get_data_source_by_name(self, name: str) -> dict:
        """
        Retrieve information about a specific data source using its name.

        Args:
            name (str): The name of the data source.

        Returns:
            dict: {
                "success": True,
                "data": DataSourceInfo
            }
            or
            {
                "success": False,
                "error": "Data source not found"
            }

        Constraints:
            - Returns the first data source that matches the name exactly (case sensitive).
            - If no matching data source is found, returns an error message.
        """
        for data_source in self.data_sources.values():
            if data_source["name"] == name:
                return {"success": True, "data": data_source}
        return {"success": False, "error": "Data source not found"}

    def search_jobs(
        self,
        keywords: list,
        location: str,
        filters: dict,
        sources: list = None
    ) -> dict:
        """
        Search for active job postings matching keywords (in title/description), location, additional filters,
        and (optionally) restricted to certain source_ids.

        Args:
            keywords (List[str]): Keywords to match (case-insensitive, in title or description, conjunctive or disjunctive).
            location (str): Location string to match (case-insensitive exact match).
            filters (Dict[str, Any]): Additional filter criteria (e.g., employment_type, salary_range).
            sources (Optional[List[str]]): List of allowed source_ids to search within
                (if None or an empty list, search all).

        Returns:
            dict: {
                "success": True,
                "data": List[JobPostingInfo],  # Matching job postings
            }
            or
            {
                "success": False,
                "error": str  # Error reason
            }

        Constraints:
            - Only active jobs are returned.
            - Jobs must match all provided filters and source (if any).
            - Keywords matched in title or description (case-insensitive, if at least one keyword matches).
            - Location is matched case-insensitively (exact).
        """
        # Input validation
        if not isinstance(keywords, list) or not isinstance(location, str) or not isinstance(filters, dict):
            return {"success": False, "error": "Invalid parameter types."}
        if sources is not None and not isinstance(sources, list):
            return {"success": False, "error": "sources must be a list or None."}

        normalized_sources = None if sources == [] else sources

        # If sources specified, check for invalid source_ids
        if normalized_sources is not None:
            invalid_sources = [sid for sid in normalized_sources if sid not in self.data_sources]
            if invalid_sources:
                return {"success": False, "error": f"Invalid source ids: {invalid_sources}"}

        matched_jobs = []
        for job in self.job_postings.values():
            # Only active jobs
            if str(job.get("status", "")).lower() != "active":
                continue

            # Source filter
            if normalized_sources is not None and job.get("source_id") not in normalized_sources:
                continue

            # Location filter: case-insensitive exact match
            if location and (str(job.get("location", "")).strip().lower() != location.strip().lower()):
                continue

            # Keyword matching: at least one keyword in title or description, case-insensitive
            job_title = job.get("title", "").lower()
            job_desc = job.get("description", "").lower()
            if keywords:
                matches = False
                for keyword in keywords:
                    k = str(keyword).lower()
                    if k in job_title or k in job_desc:
                        matches = True
                        break
                if not matches:
                    continue

            # Filters: all provided key-value pairs must match exactly
            filter_match = True
            for key, val in filters.items():
                if job.get(key) != val:
                    filter_match = False
                    break
            if not filter_match:
                continue

            matched_jobs.append(job)

        return {"success": True, "data": matched_jobs}

    def get_job_posting_by_id(self, job_id: str) -> dict:
        """
        Retrieve details of a specific job posting given its job_id.

        Args:
            job_id (str): The unique identifier for the job posting.

        Returns:
            dict:
                - { "success": True, "data": JobPostingInfo } if found.
                - { "success": False, "error": "Job posting not found" } if job_id does not exist.

        Constraints:
            - No additional constraints; status of the job posting does not affect retrieval.
        """
        job_posting = self.job_postings.get(job_id)
        if job_posting is None:
            return { "success": False, "error": "Job posting not found" }
        return { "success": True, "data": job_posting }

    def list_jobs_by_source(self, source_id: str) -> dict:
        """
        List all job postings from the given data source.

        Args:
            source_id (str): The unique identifier of the data source.

        Returns:
            dict: 
                {'success': True, 'data': List[JobPostingInfo]}  # If found (may be empty)
                or
                {'success': False, 'error': str}  # If data source does not exist

        Constraints:
            - The given source_id must correspond to an existing data source.
            - Returns all jobs from the source, regardless of status.
        """
        if source_id not in self.data_sources:
            return {"success": False, "error": "Data source does not exist"}

        jobs = [
            job_info for job_info in self.job_postings.values()
            if job_info["source_id"] == source_id
        ]

        return {"success": True, "data": jobs}

    def list_active_jobs(self, location: str = None, keywords: list = None) -> dict:
        """
        List all currently active jobs, with optional filtering by location and keywords.

        Args:
            location (str, optional): Only include jobs at this location (case-insensitive exact match).
            keywords (List[str], optional): Only include jobs where at least one keyword appears
                                             in the title or description (case-insensitive substring match).

        Returns:
            dict:
                {
                    "success": True,
                    "data": [JobPostingInfo, ...]  # May be empty if no matches
                }
                or
                {
                    "success": False,
                    "error": str  # Description of the error/reason
                }
        
        Constraints:
            - Only jobs with status == "active" are included.
            - Location filter is case-insensitive exact match.
            - If keywords is provided, at least one keyword must appear in the title or description
              (case-insensitive substring match).
        """
        # Parameter validation
        if keywords is not None and not isinstance(keywords, list):
            return { "success": False, "error": "keywords parameter must be a list of strings" }
        if keywords is not None:
            for k in keywords:
                if not isinstance(k, str):
                    return { "success": False, "error": "Each keyword in keywords must be a string" }

        result = []
        for job in self.job_postings.values():
            if str(job.get("status", "")).lower() != "active":
                continue
            # Location filter
            if location is not None:
                if not isinstance(job.get("location", ""), str):
                    continue
                if job["location"].strip().lower() != location.strip().lower():
                    continue
            # Keyword filter
            if keywords:
                job_text = (job.get("title", "") + " " + job.get("description", "")).lower()
                if not any(kw.lower() in job_text for kw in keywords):
                    continue
            result.append(job)

        return { "success": True, "data": result }

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve the profile and settings for a user.

        Args:
            user_id (str): The ID of the user to lookup.

        Returns:
            dict:
                If the user exists:
                    {
                      "success": True,
                      "data": UserInfo   # User preferences, search_history, comparison_history
                    }
                If not found:
                    {
                      "success": False,
                      "error": "User not found"
                    }

        Constraints:
            - user_id must exist in self.users.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": self.users[user_id] }

    def list_user_search_history(self, user_id: str) -> dict:
        """
        Retrieve all historical search queries for the given user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict:
                - success: True and data: List[SearchQueryInfo] if successful.
                - success: False and error message otherwise.

        Constraints:
            - User must exist.
            - Returned data includes only SearchQueryInfo for query_ids present in user search_history and in self.search_queries.
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }

        history_query_ids = user.get("search_history", [])
        queries = [
            self.search_queries[qid]
            for qid in history_query_ids
            if qid in self.search_queries
        ]
        return { "success": True, "data": queries }

    def list_user_comparison_history(self, user_id: str) -> dict:
        """
        Retrieve a user's job comparison history.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": List[str]  # List of job_id pairs, job_id strings, or custom identifiers
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g. user not found
            }

        Constraints:
            - user_id must exist in self.users.
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User not found" }
    
        # Always return the (possibly empty) comparison_history list
        return { "success": True, "data": user.get("comparison_history", []) }

    def get_search_query_by_id(self, query_id: str) -> dict:
        """
        Retrieve the full record of a past search query by its query_id.

        Args:
            query_id (str): The identifier for the search query.

        Returns:
            dict: {
                "success": True,
                "data": SearchQueryInfo  # Search query record
            }
            or
            {
                "success": False,
                "error": "Search query not found"
            }

        Constraints:
            - The specified query_id must exist in the search_queries.
        """
        if query_id not in self.search_queries:
            return { "success": False, "error": "Search query not found" }
        return { "success": True, "data": self.search_queries[query_id] }

    def compare_job_postings(self, job_ids: list[str]) -> dict:
        """
        Compare two or more job postings, returning their title, company, location,
        employment type, and salary range for comparison. Only includes postings that are active.

        Args:
            job_ids (List[str]): List of job posting IDs to compare.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "data": List[Dict[str, str]],  # Comparison info for each found and active job
                    "inactive_jobs": List[str],    # List of job_ids found but not active (optional, may be empty)
                    "not_found": List[str],        # List of job_ids not found (optional, may be empty)
                }
                On error (no valid jobs found):
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - Only active (status=="active") postings are included in the comparison.
        """
        if not job_ids or not isinstance(job_ids, list):
            return {"success": False, "error": "job_ids must be a non-empty list."}

        job_ids = list(set(job_ids))  # Remove duplicates if any

        comparison_data = []
        not_found = []
        inactive_jobs = []

        for job_id in job_ids:
            job = self.job_postings.get(job_id)
            if job is None:
                not_found.append(job_id)
                continue
            if job['status'] != 'active':
                inactive_jobs.append(job_id)
                continue
            comparison_data.append({
                "job_id": job["job_id"],
                "title": job["title"],
                "company": job["company"],
                "location": job["location"],
                "employment_type": job.get("employment_type", ""),
                "salary_range": job.get("salary_range", ""),
                "source_id": job.get("source_id", ""),
                "date_posted": job.get("date_posted", ""),
                "url": job.get("url", "")
            })

        if not comparison_data:
            return {
                "success": False,
                "error": "No valid (active) job postings found for the given job_ids.",
                "inactive_jobs": inactive_jobs,
                "not_found": not_found
            }

        return {
            "success": True,
            "data": comparison_data,
            "inactive_jobs": inactive_jobs,
            "not_found": not_found
        }

    def check_job_posting_status(self, job_id: str) -> dict:
        """
        Query the current status (e.g., active, expired) of a job posting.

        Args:
            job_id (str): The unique identifier for the job posting to check.

        Returns:
            dict: 
                Success: { "success": True, "data": { "job_id": job_id, "status": status } }
                Failure: { "success": False, "error": "Job posting not found" }
    
        Constraints:
            - The job posting must exist in the system.
        """
        job = self.job_postings.get(job_id)
        if not job:
            return { "success": False, "error": "Job posting not found" }
        return {
            "success": True,
            "data": {
                "job_id": job_id,
                "status": job["status"],
            }
        }

    def store_user_search_query(
        self,
        user_id: str,
        query_id: str,
        keywords: list,
        location: str,
        date_created: str,
        filters: dict
    ) -> dict:
        """
        Save a new search query for a user and update the user's search history.

        Args:
            user_id (str): The unique ID of the user making the search.
            query_id (str): The unique ID to assign to the new search query.
            keywords (List[str]): Keywords for job search.
            location (str): Location filter.
            date_created (str): Timestamp for query creation.
            filters (Dict[str, Any]): Additional filter criteria.

        Returns:
            dict: {
                "success": True,
                "message": "Search query stored and user history updated"
            }
            or
            {
                "success": False,
                "error": "<error reason>"
            }

        Constraints:
            - user_id must correspond to an existing user.
            - query_id must not already exist in self.search_queries.
        """
        # Validate user_id exists
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        # Check query_id uniqueness
        if query_id in self.search_queries:
            return { "success": False, "error": "Query ID already exists" }

        # Basic input type checking (robustness)
        if not isinstance(keywords, list):
            return { "success": False, "error": "Keywords must be a list" }
        if not isinstance(filters, dict):
            return { "success": False, "error": "Filters must be a dictionary" }
        if not isinstance(location, str) or not location:
            return { "success": False, "error": "Location must be a non-empty string" }

        # Construct the SearchQueryInfo object
        search_query: SearchQueryInfo = {
            "query_id": query_id,
            "user_id": user_id,
            "keywords": keywords,
            "location": location,
            "date_created": date_created,
            "filters": filters
        }

        # Store the search query
        self.search_queries[query_id] = search_query

        # Update user search history
        user_info = self.users[user_id]
        user_info["search_history"].append(query_id)
        self.users[user_id] = user_info

        return { "success": True, "message": "Search query stored and user history updated" }

    def add_to_user_comparison_history(self, user_id: str, comparison_entry: str) -> dict:
        """
        Store a new job comparison event in the user's comparison history.
    
        Args:
            user_id (str): ID of the user whose history will be updated.
            comparison_entry (str): Representation of the job comparison event (job_id(s) or pair, as per environment).

        Returns:
            dict: {
                "success": True,
                "message": "Comparison entry added to user's comparison history"
            }
            or
            {
                "success": False,
                "error": "User not found"
            }
    
        Constraints:
            - User must exist in the platform.
            - No format checking is performed on comparison_entry (accepts as string).
        """
        if user_id not in self.users:
            return {"success": False, "error": "User not found"}

        self.users[user_id]["comparison_history"].append(comparison_entry)
        return {"success": True, "message": "Comparison entry added to user's comparison history"}

    def expire_job_posting(self, job_id: str) -> dict:
        """
        Change the status of a job posting to 'expired'.

        Args:
            job_id (str): The unique identifier for the job posting to update.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Job posting {job_id} marked as expired." }
                - On failure: { "success": False, "error": "Job posting not found." }

        Constraints:
            - The job posting must exist in the system.
            - Idempotent operation: If already expired, still succeed.
        """
        if job_id not in self.job_postings:
            return { "success": False, "error": "Job posting not found." }

        self.job_postings[job_id]['status'] = "expired"

        return { "success": True, "message": f"Job posting {job_id} marked as expired." }

    def sync_data_source_jobs(self, source_id: str) -> dict:
        """
        Update (simulate aggregation/sync) the job postings from a specific data source.

        Args:
            source_id (str): The identifier of the data source to sync.

        Returns:
            dict: {
                'success': True,
                'message': str,  # Describes the result of the sync
            }
            or
            {
                'success': False,
                'error': str  # Error message if source_id not found or other errors
            }

        Constraints:
            - Data source with `source_id` must exist.
            - On sync, data source's `last_synced` field is updated to current time.
            - In a real setting, new/updated job postings from the source would be merged in.
        """

        if source_id not in self.data_sources:
            return {
                "success": False,
                "error": f"Data source with id '{source_id}' does not exist"
            }

        # Update last_synced to now
        self.data_sources[source_id]['last_synced'] = str(int(time.time()))

        # Here, we would fetch and update self.job_postings from the data source.
        # For simulation, do nothing or simulate updating existing/mocking a change.

        return {
            "success": True,
            "message": f"Job postings updated from data source {source_id}"
        }

    def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> dict:
        """
        Update or add new settings in the specified user's preferences.

        Args:
            user_id (str): The ID of the user whose preferences should be updated.
            preferences (Dict[str, Any]): The new or updated preferences to store (will merge with existing preferences).

        Returns:
            dict: {
                "success": True,
                "message": "Preferences updated for user <user_id>"
            }
            or
            {
                "success": False,
                "error": str  # Error explanation (e.g., user does not exist; preferences not a dict)
            }

        Constraints:
            - user_id must exist in users.
            - preferences must be a dictionary.
            - Existing preferences are updated/merged; new keys are added; other keys remain unchanged.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        if not isinstance(preferences, dict):
            return {"success": False, "error": "Preferences must be a dictionary"}

        current_preferences = self.users[user_id].get("preferences", {})
        current_preferences.update(preferences)
        self.users[user_id]["preferences"] = current_preferences

        return {"success": True, "message": f"Preferences updated for user {user_id}"}

    def remove_job_posting(self, job_id: str) -> dict:
        """
        Delete a job posting from the system, including cleaning up references in user comparison histories.

        Args:
            job_id (str): The identifier of the job posting to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Job posting removed"
            }
            or
            {
                "success": False,
                "error": "Job posting does not exist"
            }

        Constraints:
            - The job posting must exist.
            - Remove all references to this job_id from users' comparison_history.
        """
        if job_id not in self.job_postings:
            return { "success": False, "error": "Job posting does not exist" }

        # Remove the job posting itself
        del self.job_postings[job_id]

        # Clean up: remove references in any user's comparison_history
        for user_info in self.users.values():
            new_history = []
            for entry in user_info["comparison_history"]:
                if isinstance(entry, (list, tuple)):
                    if job_id not in entry:
                        new_history.append(entry)
                else:
                    entry_text = str(entry)
                    pattern = rf'(^|[^A-Za-z0-9_]){re.escape(job_id)}([^A-Za-z0-9_]|$)'
                    if not re.search(pattern, entry_text):
                        new_history.append(entry)
            user_info["comparison_history"] = new_history

        return { "success": True, "message": "Job posting removed" }

    def update_job_posting(self, job_id: str, updates: dict) -> dict:
        """
        Edit details or status of an existing job posting.

        Args:
            job_id (str): The unique identifier of the job posting to update.
            updates (dict): A mapping from field name to new value. Only fields present in JobPostingInfo can be updated.

        Returns:
            dict:
                - On success: {"success": True, "message": "Job posting <job_id> updated."}
                - On failure: {"success": False, "error": <reason>}

        Constraints:
            - job_id must exist in the platform.
            - Only keys from JobPostingInfo may be updated; ignore or fail if invalid.
        """
        if job_id not in self.job_postings:
            return {"success": False, "error": "Job posting not found"}

        valid_fields = set(JobPostingInfo.__annotations__.keys())
        invalid_fields = [k for k in updates if k not in valid_fields]
        if invalid_fields:
            return {
                "success": False,
                "error": f"Invalid fields for update: {', '.join(invalid_fields)}"
            }

        self.job_postings[job_id].update({k: v for k, v in updates.items() if k in valid_fields})

        return {"success": True, "message": f"Job posting {job_id} updated."}


class JobAggregatorPlatform(BaseEnv):
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

    def list_data_sources(self, **kwargs):
        return self._call_inner_tool('list_data_sources', kwargs)

    def get_data_source_by_name(self, **kwargs):
        return self._call_inner_tool('get_data_source_by_name', kwargs)

    def search_jobs(self, **kwargs):
        return self._call_inner_tool('search_jobs', kwargs)

    def get_job_posting_by_id(self, **kwargs):
        return self._call_inner_tool('get_job_posting_by_id', kwargs)

    def list_jobs_by_source(self, **kwargs):
        return self._call_inner_tool('list_jobs_by_source', kwargs)

    def list_active_jobs(self, **kwargs):
        return self._call_inner_tool('list_active_jobs', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def list_user_search_history(self, **kwargs):
        return self._call_inner_tool('list_user_search_history', kwargs)

    def list_user_comparison_history(self, **kwargs):
        return self._call_inner_tool('list_user_comparison_history', kwargs)

    def get_search_query_by_id(self, **kwargs):
        return self._call_inner_tool('get_search_query_by_id', kwargs)

    def compare_job_postings(self, **kwargs):
        return self._call_inner_tool('compare_job_postings', kwargs)

    def check_job_posting_status(self, **kwargs):
        return self._call_inner_tool('check_job_posting_status', kwargs)

    def store_user_search_query(self, **kwargs):
        return self._call_inner_tool('store_user_search_query', kwargs)

    def add_to_user_comparison_history(self, **kwargs):
        return self._call_inner_tool('add_to_user_comparison_history', kwargs)

    def expire_job_posting(self, **kwargs):
        return self._call_inner_tool('expire_job_posting', kwargs)

    def sync_data_source_jobs(self, **kwargs):
        return self._call_inner_tool('sync_data_source_jobs', kwargs)

    def update_user_preferences(self, **kwargs):
        return self._call_inner_tool('update_user_preferences', kwargs)

    def remove_job_posting(self, **kwargs):
        return self._call_inner_tool('remove_job_posting', kwargs)

    def update_job_posting(self, **kwargs):
        return self._call_inner_tool('update_job_posting', kwargs)
