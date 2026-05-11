# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
from datetime import datetime



class ArticleInfo(TypedDict):
    article_id: str
    title: str
    abstract: str
    keyword: str

class AuthorInfo(TypedDict):
    author_id: str
    name: str
    affiliation: str

class JournalInfo(TypedDict):
    journal_id: str
    name: str
    publish: str

class StatusHistoryEntry(TypedDict):
    status: str
    timestamp: str  # ISO string or datetime, precision left for later

class SubmissionInfo(TypedDict):
    submission_id: str
    article_id: str
    journal_id: str
    submit_date: str
    status: str
    status_history: List[StatusHistoryEntry]

class ArticleAuthorInfo(TypedDict):
    article_id: str
    author_id: str
    role: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Article Submission Management System stateful environment.
        """
        # Articles: {article_id: ArticleInfo}
        self.articles: Dict[str, ArticleInfo] = {}

        # Authors: {author_id: AuthorInfo}
        self.authors: Dict[str, AuthorInfo] = {}

        # Journals: {journal_id: JournalInfo}
        self.journals: Dict[str, JournalInfo] = {}

        # Submissions: {submission_id: SubmissionInfo}
        self.submissions: Dict[str, SubmissionInfo] = {}

        # ArticleAuthors: List of ArticleAuthorInfo mapping article/author/role
        self.article_authors: List[ArticleAuthorInfo] = []

        # Constraints:
        # - Each submission must link to a valid article and journal.
        # - An article can have multiple submission records (for multiple journals or resubmissions).
        # - status_history must be a complete, chronological log of status changes for each submission.
        # - Authors must be uniquely identifiable and associated with institutional affiliation.
        # - Only valid statuses ("submitted", "under review", "accepted", "rejected") are recorded.

    def get_article_by_title(self, article_title: str) -> dict:
        """
        Retrieve ArticleInfo by exact article title.

        Args:
            article_title (str): The title of the article to search for.

        Returns:
            dict: {
                "success": True,
                "data": ArticleInfo  # Article metadata if found
            }
            or
            {
                "success": False,
                "error": str  # Message if not found
            }

        Constraints:
            - Title must match exactly (case-sensitive).
            - If multiple articles have the same title, the first found is returned.
        """
        for article in self.articles.values():
            if article["title"] == article_title:
                return {"success": True, "data": article}
        return {"success": False, "error": "Article with the given title not found"}

    def get_article_by_id(self, article_id: str) -> dict:
        """
        Retrieve article information by unique article_id.

        Args:
            article_id (str): The unique identifier for the article.

        Returns:
            dict:
                - If success: {"success": True, "data": ArticleInfo}
                - If article_id is missing or not found: {"success": False, "error": <reason>}

        Constraints:
            - article_id must be present and correspond to an existing article.
        """
        if not article_id or not isinstance(article_id, str):
            return { "success": False, "error": "Invalid or missing article_id" }

        article = self.articles.get(article_id)
        if not article:
            return { "success": False, "error": "Article not found" }

        return { "success": True, "data": article }

    def list_articles(self) -> dict:
        """
        List all articles currently registered in the system, with their metadata.

        Returns:
            dict: {
                "success": True,
                "data": List[ArticleInfo],  # List of all articles (may be empty)
            }
        """
        articles_list = list(self.articles.values())
        return { "success": True, "data": articles_list }

    def get_authors_by_article_id(self, article_id: str) -> dict:
        """
        List all authors and their roles for a given article.

        Args:
            article_id (str): The article's unique identifier.

        Returns:
            dict: {
                "success": True,
                "data": List[{
                    "author_id": str,
                    "name": str,
                    "affiliation": str,
                    "role": str
                }]
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - article_id must exist.
            - Only authors properly linked to the article are returned.
            - If no authors are linked, 'data' is an empty list.
        """
        if article_id not in self.articles:
            return {"success": False, "error": "Article does not exist"}

        results = []
        for aa in self.article_authors:
            if aa["article_id"] == article_id:
                author_id = aa["author_id"]
                if author_id in self.authors:
                    author = self.authors[author_id]
                    results.append({
                        "author_id": author_id,
                        "name": author["name"],
                        "affiliation": author["affiliation"],
                        "role": aa.get("role", "")
                    })
                else:
                    # Author ID in link does not exist; skip this (data integrity issue)
                    continue

        return {"success": True, "data": results}

    def get_author_by_id(self, author_id: str) -> dict:
        """
        Retrieve AuthorInfo for a given author_id.

        Args:
            author_id (str): Unique identifier of the author.

        Returns:
            dict:
                - If author is found:
                    { "success": True, "data": AuthorInfo }
                - If author is not found:
                    { "success": False, "error": "Author not found" }

        Constraints:
            - author_id must exist in the authors dictionary.
        """
        if not author_id or author_id not in self.authors:
            return { "success": False, "error": "Author not found" }

        return { "success": True, "data": self.authors[author_id] }

    def get_author_by_name(self, name: str, affiliation: str = None) -> dict:
        """
        Retrieve one or more AuthorInfo records by author name. If 'affiliation' is provided,
        only authors with that exact (case-sensitive) name and affiliation are returned.
        Otherwise, all authors matching the name are returned.

        Args:
            name (str): The author's name to search for.
            affiliation (str, optional): Disambiguate by institutional affiliation.

        Returns:
            dict: {
                "success": True,
                "data": List[AuthorInfo]  # empty list if no match
            }
        """
        if affiliation is not None:
            matches = [
                author for author in self.authors.values()
                if author["name"] == name and author["affiliation"] == affiliation
            ]
        else:
            matches = [
                author for author in self.authors.values()
                if author["name"] == name
            ]
        return {
            "success": True,
            "data": matches
        }

    def list_article_submissions(self, article_id: str) -> dict:
        """
        List all submissions associated with a given article_id.

        Args:
            article_id (str): The unique identifier of the article.

        Returns:
            dict: {
                "success": True,
                "data": List[SubmissionInfo]  # submissions for the given article_id (may be empty if none)
            }
            or
            {
                "success": False,
                "error": str  # Explanation, e.g. "Article does not exist"
            }

        Constraints:
            - The article_id must already exist in the system.
        """
        if article_id not in self.articles:
            return {"success": False, "error": "Article does not exist"}

        submissions = [
            submission for submission in self.submissions.values()
            if submission["article_id"] == article_id
        ]

        return {"success": True, "data": submissions}

    def get_submission_by_id(self, submission_id: str) -> dict:
        """
        Retrieve the complete SubmissionInfo record (including status and history) by submission_id.

        Args:
            submission_id (str): The ID of the submission to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": SubmissionInfo
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The submission_id must exist in the system.
        """
        submission = self.submissions.get(submission_id)
        if submission is None:
            return { "success": False, "error": "Submission not found" }
        return { "success": True, "data": submission }

    def get_submission_status(self, submission_id: str) -> dict:
        """
        Query the current status of a submission.

        Args:
            submission_id (str): The ID of the submission to query.

        Returns:
            dict: If found, {
                        "success": True,
                        "data": str    # Current status, e.g. "submitted", "under review", etc.
                   }
                  If not found, {
                        "success": False,
                        "error": "Submission not found"
                  }

        Constraints:
            - The submission must exist in the system.
            - Only valid statuses will be found due to enforced system rules.
        """
        submission = self.submissions.get(submission_id)
        if not submission:
            return {"success": False, "error": "Submission not found"}

        # Defensive: ensure status key exists
        status = submission.get("status")
        if status is None:
            return {"success": False, "error": "Submission status missing"}

        return {"success": True, "data": status}

    def get_submission_status_history(self, submission_id: str) -> dict:
        """
        Retrieve the full, chronological status history for a given submission.

        Args:
            submission_id (str): The unique identifier of the submission.

        Returns:
            dict: {
                "success": True,
                "data": List[StatusHistoryEntry],  # The complete status history in order (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Description, e.g., "Submission not found"
            }

        Constraints:
            - The submission with submission_id must exist.
            - status_history is returned as stored (chronological, as per constraints).
        """
        submission = self.submissions.get(submission_id)
        if not submission:
            return { "success": False, "error": "Submission not found" }

        status_history = submission.get("status_history", [])
        return { "success": True, "data": status_history }

    def get_journal_by_id(self, journal_id: str) -> dict:
        """
        Retrieve the JournalInfo for the specified journal_id.

        Args:
            journal_id (str): The unique identifier for the journal.

        Returns:
            dict: 
                { "success": True, "data": JournalInfo } if journal found,
                { "success": False, "error": str } if not found.
    
        Constraints:
            - The journal_id must exist in the system.
        """
        journal = self.journals.get(journal_id)
        if journal is None:
            return { "success": False, "error": "Journal ID not found" }
        return { "success": True, "data": journal }

    def get_journal_by_name(self, name: str) -> dict:
        """
        Retrieve a journal's information by its name.

        Args:
            name (str): The name of the journal.

        Returns:
            dict: {
                "success": True,
                "data": JournalInfo,
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Returns the first (and should be only) journal with the specified name.
            - If no such journal exists, returns an error.
        """
        if not name or not isinstance(name, str):
            return { "success": False, "error": "Journal name must be a non-empty string." }

        for journal in self.journals.values():
            if journal["name"] == name:
                return { "success": True, "data": journal }

        return { "success": False, "error": f'Journal with name "{name}" does not exist.' }

    def search_submissions_by_article_title(self, title_query: str) -> dict:
        """
        Retrieve all submissions where the associated article's title matches the query
        (case-insensitive, full or partial substring).

        Args:
            title_query (str): Partial or full title to match (case-insensitive substring).

        Returns:
            dict:
                success: True, data: List[SubmissionInfo] (empty if no matches)
                OR
                success: False, error: str description

        Constraints:
            - The query cannot be empty.
            - Matching is case-insensitive substring match.
        """
        if not isinstance(title_query, str) or not title_query.strip():
            return {"success": False, "error": "Title query must be a non-empty string."}

        query_lower = title_query.lower()
        # Find matching article IDs
        matching_article_ids = [
            article_id
            for article_id, article in self.articles.items()
            if query_lower in article["title"].lower()
        ]

        # Get all submissions for these article IDs
        result = [
            submission
            for submission in self.submissions.values()
            if submission["article_id"] in matching_article_ids
        ]

        return {"success": True, "data": result}

    def search_submissions_by_author(self, author_id: str) -> dict:
        """
        Get all submissions for articles co-authored by a specific author.

        Args:
            author_id (str): The unique identifier of the author.

        Returns:
            dict: {
                "success": True,
                "data": List[SubmissionInfo]  # All submissions for articles co-authored by the author
            }
            or
            {
                "success": False,
                "error": str  # If the author is not found
            }

        Constraints:
            - author_id must exist in the system.
            - If the author has no articles or no submissions, return empty list as data.
        """
        if author_id not in self.authors:
            return { "success": False, "error": "Author not found" }

        # Find all article_ids for this author
        article_ids = set(
            aa['article_id'] for aa in self.article_authors
            if aa['author_id'] == author_id
        )

        submissions = [
            subm for subm in self.submissions.values()
            if subm['article_id'] in article_ids
        ]

        return { "success": True, "data": submissions }

    def filter_submissions_by_status(self, status: str) -> dict:
        """
        Retrieve all submissions whose current status matches the provided status.

        Args:
            status (str): The status to filter submissions by. Valid values are
                "submitted", "under review", "accepted", "rejected".

        Returns:
            dict: {
                "success": True,
                "data": List[SubmissionInfo],  # May be empty if no submissions with the status
            }
            or
            {
                "success": False,
                "error": str  # Explanation of validation failure
            }

        Constraints:
            - Only the following status values are valid (case-sensitive):
              "submitted", "under review", "accepted", "rejected"
        """
        valid_statuses = {"submitted", "under review", "accepted", "rejected"}
        if status not in valid_statuses:
            return {
                "success": False,
                "error": f"Invalid status. Valid statuses: {', '.join(valid_statuses)}"
            }

        filtered = [
            submission
            for submission in self.submissions.values()
            if submission["status"] == status
        ]
        return {"success": True, "data": filtered}

    def add_article(self, title: str, abstract: str, keyword: str) -> dict:
        """
        Create and add a new article record with title, abstract, and keyword.

        Args:
            title (str): Title of the article (required, non-empty)
            abstract (str): Article abstract (required, non-empty)
            keyword (str): Keywords for the article (required, non-empty)

        Returns:
            dict: 
                Success:
                    { "success": True, "message": "Article created", "article_id": str }
                Failure:
                    { "success": False, "error": str }

        Constraints:
            - All fields must be non-empty.
            - article_id generated must be unique.
            - Article titles are not required to be unique.
        """
        # Validate input
        if not isinstance(title, str) or not title.strip():
            return { "success": False, "error": "Title is required and cannot be empty." }
        if not isinstance(abstract, str) or not abstract.strip():
            return { "success": False, "error": "Abstract is required and cannot be empty." }
        if not isinstance(keyword, str) or not keyword.strip():
            return { "success": False, "error": "Keyword is required and cannot be empty." }

        # Generate unique article_id, simple scheme: "ART" + zero-padded number
        idx = 1
        while True:
            article_id = f"ART{idx:05d}"
            if article_id not in self.articles:
                break
            idx += 1

        # Create article record
        article_info: ArticleInfo = {
            "article_id": article_id,
            "title": title,
            "abstract": abstract,
            "keyword": keyword
        }
        self.articles[article_id] = article_info

        return { "success": True, "message": "Article created", "article_id": article_id }

    def add_author(self, name: str, affiliation: str) -> dict:
        """
        Add a new author with the given name and institutional affiliation.

        Args:
            name (str): Author's full name.
            affiliation (str): Author's institutional affiliation.

        Returns:
            dict:
                - On success: {
                    "success": True,
                    "message": "Author added successfully.",
                    "author_id": str  # newly assigned author_id
                  }
                - On failure: {
                    "success": False,
                    "error": str  # description of error (e.g., input empty)
                  }

        Constraints:
            - Author must have a non-empty name and affiliation.
            - Author IDs are auto-generated for uniqueness.
        """
        if not name or not affiliation:
            return { "success": False, "error": "Name and affiliation must not be empty." }

        # Generate a unique author_id (simple increment or UUID). We'll use increment:
        idx = 1
        while True:
            new_author_id = f"AUTH{idx}"
            if new_author_id not in self.authors:
                break
            idx += 1

        author_info: AuthorInfo = {
            "author_id": new_author_id,
            "name": name,
            "affiliation": affiliation
        }
        self.authors[new_author_id] = author_info

        return {
            "success": True,
            "message": f"Author added successfully.",
            "author_id": new_author_id
        }

    def link_author_to_article(self, article_id: str, author_id: str, role: str) -> dict:
        """
        Create an ArticleAuthor record linking an author to an article with a given role.

        Args:
            article_id (str): ID of the article.
            author_id (str): ID of the author.
            role (str): Author's role on the article (e.g., 'first author', 'corresponding author').

        Returns:
            dict: {
                "success": True,
                "message": "Author linked to article with role."
            }
            or
            {
                "success": False,
                "error": "..."
            }

        Constraints:
            - article_id must exist in the system.
            - author_id must exist in the system.
            - (article_id, author_id, role) triple must not already exist (no duplicate link).
        """
        if article_id not in self.articles:
            return {"success": False, "error": "Article does not exist."}

        if author_id not in self.authors:
            return {"success": False, "error": "Author does not exist."}

        if not isinstance(role, str) or not role.strip():
            return {"success": False, "error": "Role must be a non-empty string."}

        # Prevent duplicate (article_id, author_id, role) links
        for link in self.article_authors:
            if link["article_id"] == article_id and link["author_id"] == author_id and link["role"] == role:
                return {"success": False, "error": "This author is already linked to the article with that role."}

        self.article_authors.append({
            "article_id": article_id,
            "author_id": author_id,
            "role": role
        })

        return {"success": True, "message": "Author linked to article with role."}

    def add_journal(self, journal_id: str, name: str, publish: str) -> dict:
        """
        Add a new journal to the system.

        Args:
            journal_id (str): Unique identifier for the journal.
            name (str): Name of the journal.
            publish (str): Publishing entity of the journal.

        Returns:
            dict: {
                "success": True,
                "message": "Journal added successfully."
            }
            or
            {
                "success": False,
                "error": str  # Description of the error; e.g., duplicate journal_id or missing required field
            }

        Constraints:
            - journal_id must be unique.
            - All fields must be non-empty.
        """
        if not journal_id or not name or not publish:
            return {"success": False, "error": "All fields (journal_id, name, publish) are required and cannot be empty."}
        if journal_id in self.journals:
            return {"success": False, "error": "Journal ID already exists."}
    
        journal_info = {
            "journal_id": journal_id,
            "name": name,
            "publish": publish
        }
        self.journals[journal_id] = journal_info
        return {"success": True, "message": "Journal added successfully."}

    def create_submission(
        self,
        submission_id: str,
        article_id: str,
        journal_id: str,
        submit_date: str,
        status: str
    ) -> dict:
        """
        Create a new submission record, linking article, journal, and setting initial status/history.

        Args:
            submission_id (str): Unique identifier for the submission.
            article_id (str): ID of the article being submitted (must exist).
            journal_id (str): ID of the journal to which the article is being submitted (must exist).
            submit_date (str): Submission date (ISO string).
            status (str): Initial status for the submission ("submitted", "under review", "accepted", "rejected").

        Returns:
            dict: On success: { "success": True, "message": "Submission created successfully" }
                  On error:   { "success": False, "error": <str> }

        Constraints:
            - submission_id must be unique.
            - article_id and journal_id must exist.
            - status must be one of ["submitted", "under review", "accepted", "rejected"].
            - Initial status_history must contain this first status and timestamp.
        """
        VALID_STATUSES = {"submitted", "under review", "accepted", "rejected"}

        if submission_id in self.submissions:
            return { "success": False, "error": "Submission ID already exists." }

        if article_id not in self.articles:
            return { "success": False, "error": "Article ID does not exist." }

        if journal_id not in self.journals:
            return { "success": False, "error": "Journal ID does not exist." }

        if status not in VALID_STATUSES:
            return { "success": False, "error": f"Invalid status '{status}'. Must be one of {sorted(VALID_STATUSES)}." }

        if not submit_date or not isinstance(submit_date, str):
            return { "success": False, "error": "Invalid or missing submit_date." }

        submission_info = {
            "submission_id": submission_id,
            "article_id": article_id,
            "journal_id": journal_id,
            "submit_date": submit_date,
            "status": status,
            "status_history": [
                {"status": status, "timestamp": submit_date}
            ]
        }
        self.submissions[submission_id] = submission_info
        return { "success": True, "message": "Submission created successfully" }


    def update_submission_status(self, submission_id: str, new_status: str, timestamp: str = None) -> dict:
        """
        Change the status of a submission and append the change to its status_history,
        enforcing allowed status values.

        Args:
            submission_id (str): The ID of the submission to update.
            new_status (str): The new status value (must be one of allowed statuses).
            timestamp (str, optional): ISO timestamp for the status change. If not provided, current time is used.

        Returns:
            dict: {
                "success": True,
                "message": "Submission status updated to <new_status>"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Only valid statuses ("submitted", "under review", "accepted", "rejected") are allowed.
            - Submission must exist.
            - Status history must be appended in chronological order.
        """
        allowed_statuses = {"submitted", "under review", "accepted", "rejected"}

        if submission_id not in self.submissions:
            return {"success": False, "error": "Submission ID does not exist"}
        if new_status not in allowed_statuses:
            return {"success": False, "error": f"Invalid status '{new_status}'. Allowed: {sorted(allowed_statuses)}"}

        if timestamp is None:
            timestamp = datetime.now().isoformat()

        submission = self.submissions[submission_id]
        # Append to status_history
        status_entry = {
            "status": new_status,
            "timestamp": timestamp
        }
        submission["status"] = new_status
        submission["status_history"].append(status_entry)

        return {
            "success": True,
            "message": f"Submission status updated to '{new_status}'"
        }

    def correct_status_history_entry(
        self,
        submission_id: str,
        entry_index: int,
        new_status: str,
        new_timestamp: str
    ) -> dict:
        """
        Correct a previous status entry in the status_history of a submission.
        Maintains an audit trail by appending a new status entry indicating that
        a correction was made, rather than replacing the historical log.

        Args:
            submission_id (str): ID of the submission to correct.
            entry_index (int): Index in status_history of the entry to correct.
            new_status (str): The corrected status (must be valid).
            new_timestamp (str): Timestamp for the correction.

        Returns:
            dict: { "success": True, "message": "Correction appended..." }
                  or { "success": False, "error": "reason" }

        Constraints:
            - Only valid statuses allowed: "submitted", "under review", "accepted", "rejected"
            - status_history audit trail is maintained: the original entry is never erased, instead a correction is appended.
            - entry_index must exist in status_history.
        """
        ALLOWED_STATUSES = {"submitted", "under review", "accepted", "rejected"}

        # Check submission exists
        submission = self.submissions.get(submission_id)
        if not submission:
            return { "success": False, "error": "Submission not found" }

        sh = submission["status_history"]

        # Check entry_index valid
        if not isinstance(entry_index, int) or entry_index < 0 or entry_index >= len(sh):
            return { "success": False, "error": "Invalid status_history entry_index" }

        if new_status not in ALLOWED_STATUSES:
            return { "success": False, "error": f"Invalid status: {new_status}" }

        # Append a correction entry, do NOT overwrite existing log.
        sh.append({
            "status": new_status,
            "timestamp": new_timestamp
        })

        # The submission's current status should reflect the most recent, so update as well.
        submission["status"] = new_status

        return {
            "success": True,
            "message": (
                f"Correction for status_history entry {entry_index} "
                f"appended as new entry and status updated."
            )
        }

    def edit_article_metadata(
        self, 
        article_id: str, 
        title: str = None, 
        abstract: str = None, 
        keyword: str = None
    ) -> dict:
        """
        Update article information fields (title, abstract, keyword) for a given article_id.
    
        Args:
            article_id (str): The unique identifier of the article to be updated.
            title (str, optional): New title. If None, title is not changed.
            abstract (str, optional): New abstract. If None, abstract is not changed.
            keyword (str, optional): New keyword string. If None, keywords are not changed.
        
        Returns:
            dict:
                - success: True/False
                - message: If successful, describes update.
                - error: If unsuccessful, error reason (e.g., article not found).
    
        Constraints:
            - Article must exist in the system.
            - Only provided (non-None) fields are updated.
            - No field validation beyond existence.
        """
        if article_id not in self.articles:
            return { "success": False, "error": "Article not found." }

        article = self.articles[article_id]

        if title is not None:
            article["title"] = title
        if abstract is not None:
            article["abstract"] = abstract
        if keyword is not None:
            article["keyword"] = keyword

        # Save back (not strictly necessary for mutable dicts, but explicit for clarity)
        self.articles[article_id] = article

        return { "success": True, "message": "Article metadata updated successfully." }

    def edit_author_affiliation(self, author_id: str, new_affiliation: str) -> dict:
        """
        Update an author's institutional affiliation.

        Args:
            author_id (str): The identifier of the author whose affiliation is to be changed.
            new_affiliation (str): The new institutional affiliation.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "message": "Affiliation updated successfully."
                }
                On failure:
                {
                    "success": False,
                    "error": <error message>
                }

        Constraints:
            - The author_id must exist in the system.
            - The new_affiliation must be a non-empty string.
        """
        # Check for author existence
        author = self.authors.get(author_id)
        if author is None:
            return { "success": False, "error": "Author not found." }

        # Validate new affiliation string
        if not isinstance(new_affiliation, str) or not new_affiliation.strip():
            return { "success": False, "error": "Invalid affiliation provided." }

        # Update the affiliation
        author['affiliation'] = new_affiliation.strip()

        return { "success": True, "message": "Affiliation updated successfully." }

    def remove_article_author_link(self, article_id: str, author_id: str) -> dict:
        """
        Remove all ArticleAuthor mapping(s) for a given article_id and author_id.

        Args:
            article_id (str): The article's unique identifier.
            author_id (str): The author's unique identifier.

        Returns:
            dict: {
                "success": True,
                "message": str  # Success message
            }
            or
            {
                "success": False,
                "error": str  # Description of the error
            }

        Constraints:
            - Removes all mappings between article_id and author_id in self.article_authors.
            - Does not remove article or author records themselves.
            - If no such mapping exists, returns a failure response.
        """
        before_count = len(self.article_authors)
        self.article_authors = [
            aa for aa in self.article_authors
            if not (aa["article_id"] == article_id and aa["author_id"] == author_id)
        ]
        after_count = len(self.article_authors)

        removed_count = before_count - after_count

        if removed_count == 0:
            return {"success": False, "error": "ArticleAuthor mapping not found."}

        return {
            "success": True,
            "message": f"Removed {removed_count} ArticleAuthor mapping(s) for article_id '{article_id}' and author_id '{author_id}'."
        }

    def remove_submission(self, submission_id: str) -> dict:
        """
        Delete/cancel a submission record.

        Args:
            submission_id (str): The unique identifier of the submission to delete.

        Returns:
            dict: 
                {
                    "success": True,
                    "message": "Submission <id> removed successfully."
                }
                or
                {
                    "success": False,
                    "error": "Submission not found."
                }

        Constraints:
            - Submission must exist.
            - No status checks are required by the environment rules.
            - Only the submission record is deleted; no cascading deletes.
        """
        if submission_id not in self.submissions:
            return { "success": False, "error": "Submission not found." }
        del self.submissions[submission_id]
        return { "success": True, "message": f"Submission {submission_id} removed successfully." }

    def remove_article(self, article_id: str) -> dict:
        """
        Remove an article and all associated relationships (submissions and
        article-author links). Does not remove authors or journals.

        Args:
            article_id (str): The ID of the article to remove.

        Returns:
            dict: Success message or error, e.g.
                { "success": True, "message": "Article and associated records removed." }
                { "success": False, "error": "Article not found" }

        Constraints:
            - Removes all ArticleAuthorInfo and SubmissionInfo objects referencing the article.
            - Does NOT remove author or journal records.
        """
        if article_id not in self.articles:
            return { "success": False, "error": "Article not found" }

        # Remove the article itself
        del self.articles[article_id]

        # Remove all ArticleAuthor links for this article
        self.article_authors = [
            aa for aa in self.article_authors if aa["article_id"] != article_id
        ]

        # Remove all submissions related to this article
        self.submissions = {
            sub_id: sub
            for sub_id, sub in self.submissions.items()
            if sub["article_id"] != article_id
        }

        return { "success": True, "message": "Article and associated records removed." }


class ArticleSubmissionManagementSystem(BaseEnv):
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

    def get_article_by_title(self, **kwargs):
        return self._call_inner_tool('get_article_by_title', kwargs)

    def get_article_by_id(self, **kwargs):
        return self._call_inner_tool('get_article_by_id', kwargs)

    def list_articles(self, **kwargs):
        return self._call_inner_tool('list_articles', kwargs)

    def get_authors_by_article_id(self, **kwargs):
        return self._call_inner_tool('get_authors_by_article_id', kwargs)

    def get_author_by_id(self, **kwargs):
        return self._call_inner_tool('get_author_by_id', kwargs)

    def get_author_by_name(self, **kwargs):
        return self._call_inner_tool('get_author_by_name', kwargs)

    def list_article_submissions(self, **kwargs):
        return self._call_inner_tool('list_article_submissions', kwargs)

    def get_submission_by_id(self, **kwargs):
        return self._call_inner_tool('get_submission_by_id', kwargs)

    def get_submission_status(self, **kwargs):
        return self._call_inner_tool('get_submission_status', kwargs)

    def get_submission_status_history(self, **kwargs):
        return self._call_inner_tool('get_submission_status_history', kwargs)

    def get_journal_by_id(self, **kwargs):
        return self._call_inner_tool('get_journal_by_id', kwargs)

    def get_journal_by_name(self, **kwargs):
        return self._call_inner_tool('get_journal_by_name', kwargs)

    def search_submissions_by_article_title(self, **kwargs):
        return self._call_inner_tool('search_submissions_by_article_title', kwargs)

    def search_submissions_by_author(self, **kwargs):
        return self._call_inner_tool('search_submissions_by_author', kwargs)

    def filter_submissions_by_status(self, **kwargs):
        return self._call_inner_tool('filter_submissions_by_status', kwargs)

    def add_article(self, **kwargs):
        return self._call_inner_tool('add_article', kwargs)

    def add_author(self, **kwargs):
        return self._call_inner_tool('add_author', kwargs)

    def link_author_to_article(self, **kwargs):
        return self._call_inner_tool('link_author_to_article', kwargs)

    def add_journal(self, **kwargs):
        return self._call_inner_tool('add_journal', kwargs)

    def create_submission(self, **kwargs):
        return self._call_inner_tool('create_submission', kwargs)

    def update_submission_status(self, **kwargs):
        return self._call_inner_tool('update_submission_status', kwargs)

    def correct_status_history_entry(self, **kwargs):
        return self._call_inner_tool('correct_status_history_entry', kwargs)

    def edit_article_metadata(self, **kwargs):
        return self._call_inner_tool('edit_article_metadata', kwargs)

    def edit_author_affiliation(self, **kwargs):
        return self._call_inner_tool('edit_author_affiliation', kwargs)

    def remove_article_author_link(self, **kwargs):
        return self._call_inner_tool('remove_article_author_link', kwargs)

    def remove_submission(self, **kwargs):
        return self._call_inner_tool('remove_submission', kwargs)

    def remove_article(self, **kwargs):
        return self._call_inner_tool('remove_article', kwargs)
