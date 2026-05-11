# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
from datetime import datetime, timedelta, timezone
import uuid



class CodeSnippetInfo(TypedDict):
    snippet_id: str
    content: str
    language_id: str
    author_id: str
    created_at: str
    updated_at: str
    is_public: bool

class ProgrammingLanguageInfo(TypedDict):
    language_id: str
    name: str
    version: str
    is_supported: bool

class UserInfo(TypedDict):
    user_id: str  # From '_id'
    username: str
    account_type: str
    registration_date: str

class SubmissionHistoryInfo(TypedDict):
    mission_id: str
    snippet_id: str
    user_id: str
    timestamp: str
    action_type: str  # created/edited/executed/deleted
    result: str
    runtime_info: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Code Snippets: {snippet_id: CodeSnippetInfo}
        self.code_snippets: Dict[str, CodeSnippetInfo] = {}
        # Programming Languages: {language_id: ProgrammingLanguageInfo}
        self.programming_languages: Dict[str, ProgrammingLanguageInfo] = {}
        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}
        # Submission History: {mission_id: SubmissionHistoryInfo}
        self.submission_history: Dict[str, SubmissionHistoryInfo] = {}

        # Virtual current time for deterministic case execution.
        self.current_time: str = "2023-10-26T12:00:00Z"
        self._event_counter: int = 0

        # Constraints:
        # - Each code snippet must have a valid associated programming language.
        # - Search results must respect code snippet visibility (e.g., only public or user-accessible snippets are shown).
        # - Only supported programming languages can be selected for categorizing or filtering code snippets.
        # - Users may only edit or delete their own code snippets unless granted additional permissions.

    def _parse_current_time(self) -> datetime:
        raw = getattr(self, "current_time", "2023-10-26T12:00:00Z")
        if isinstance(raw, datetime):
            dt = raw
        elif isinstance(raw, (int, float)):
            dt = datetime.fromtimestamp(raw, tz=timezone.utc)
        elif isinstance(raw, str):
            normalized = raw.replace("Z", "+00:00") if raw.endswith("Z") else raw
            try:
                dt = datetime.fromisoformat(normalized)
            except ValueError:
                dt = datetime(2023, 10, 26, 12, 0, 0, tzinfo=timezone.utc)
        else:
            dt = datetime(2023, 10, 26, 12, 0, 0, tzinfo=timezone.utc)

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    def _next_event_timestamp(self) -> str:
        base = self._parse_current_time()
        ts = base + timedelta(seconds=self._event_counter)
        self._event_counter += 1
        return ts.isoformat().replace("+00:00", "Z")

    def _latest_failure_record(self, snippet_id: str) -> dict | None:
        failure_markers = ("timeout", "failed", "error", "resource limit exceeded", "crash")
        latest = None
        for record in self.submission_history.values():
            if record.get("snippet_id") != snippet_id:
                continue
            result = str(record.get("result", "")).lower()
            runtime = str(record.get("runtime_info", "")).lower()
            if any(marker in result or marker in runtime for marker in failure_markers):
                latest = record
        return latest

    def _infer_execution_outcome(self, snippet: dict, language_name: str) -> tuple[str, str]:
        content = str(snippet.get("content", ""))
        content_lower = content.lower()
        failure_record = self._latest_failure_record(snippet["snippet_id"])

        suspicious_patterns = (
            "while true",
            "allocate_mem",
            "stress_test",
            "cpu spike",
            "routing loop",
            "/ 0",
        )
        content_looks_risky = any(pattern in content_lower for pattern in suspicious_patterns)

        if failure_record is not None and content_looks_risky:
            return (
                str(failure_record.get("result", "Failed")),
                str(failure_record.get("runtime_info", "Execution failed.")),
            )

        if "while true" in content_lower or "allocate_mem" in content_lower or "stress_test" in content_lower:
            return ("Timeout", "Execution exceeded resource limits (simulated).")

        if "/ 0" in content_lower:
            return ("Error: ZeroDivisionError", "Traceback (most recent call last)...")

        if "routing loop" in content_lower or "return 'fail'" in content_lower or 'return "fail"' in content_lower:
            return ("Error: Routing loop detected", "Crash, Timeout after 5.00s")

        return (
            f"Executed code in language {language_name}.",
            "Execution finished in 0.01s (simulated).",
        )

    def get_programming_language_by_name(self, name: str) -> dict:
        """
        Retrieve programming language info by its name.

        Args:
            name (str): The name of the programming language (case-sensitive exact match).

        Returns:
            dict:
                - On success:
                    {
                      "success": True,
                      "data": ProgrammingLanguageInfo
                    }
                - On failure:
                    {
                      "success": False,
                      "error": "Programming language not found"
                    }

        Constraints:
            - Language with the given name must exist.
            - If multiple languages have the same name, returns the first found.
        """
        for lang in self.programming_languages.values():
            if lang["name"] == name:
                return {
                    "success": True,
                    "data": lang
                }
        return {
            "success": False,
            "error": "Programming language not found"
        }

    def list_supported_programming_languages(self) -> dict:
        """
        Retrieve all programming languages that are currently supported (is_supported == True).

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[ProgrammingLanguageInfo],  # List of supported programming languages (can be empty)
            }

        Constraints:
            - Only languages with is_supported == True are returned.
        """
        supported_langs = [
            lang_info for lang_info in self.programming_languages.values()
            if lang_info.get("is_supported", False)
        ]
        return { "success": True, "data": supported_langs }

    def get_snippets_by_language(self, language_id: str, requesting_user_id: str) -> dict:
        """
        Retrieve all code snippets filtered by a specific programming language,
        considering snippet visibility. Only public snippets or those owned by the
        requesting user are returned.

        Args:
            language_id (str): The programming language identifier to filter on.
            requesting_user_id (str): The user performing the query (used for visibility checks).

        Returns:
            dict: {
                "success": True,
                "data": List[CodeSnippetInfo]  # May be empty
            }
            or {
                "success": False,
                "error": str
            }

        Constraints:
            - The language must exist and be supported.
            - A snippet is shown if it is public, or if its author_id==requesting_user_id.
        """
        lang = self.programming_languages.get(language_id)
        if not lang:
            return { "success": False, "error": f"Programming language '{language_id}' does not exist" }
        if not lang.get("is_supported", False):
            return { "success": False, "error": f"Programming language '{language_id}' is not supported" }

        # Filter code snippets
        result = [
            snippet for snippet in self.code_snippets.values()
            if snippet["language_id"] == language_id and (
                snippet["is_public"] or snippet["author_id"] == requesting_user_id
            )
        ]
        return { "success": True, "data": result }

    def get_snippet_by_id(self, snippet_id: str) -> dict:
        """
        Retrieve a specific code snippet’s full details by snippet_id.

        Args:
            snippet_id (str): The unique identifier of the code snippet.

        Returns:
            dict:
                - On success: {"success": True, "data": CodeSnippetInfo}
                - On failure: {"success": False, "error": "Snippet not found"}

        Constraints:
            - The snippet_id must exist in the platform.
        """
        snippet = self.code_snippets.get(snippet_id)
        if snippet is None:
            return {"success": False, "error": "Snippet not found"}
        return {"success": True, "data": snippet}

    def search_snippets_by_content(self, keywords: str, user_id: str) -> dict:
        """
        Search code snippets by content substrings, filtered by snippet visibility for the querying user.

        Args:
            keywords (str): Keyword(s) to search for in code snippet content (case-insensitive).
            user_id (str): The ID of the user performing the search, to filter private/public snippets.

        Returns:
            dict: {
                "success": True,
                "data": List[CodeSnippetInfo]  # Snippets matching the query and visibility
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., user does not exist
            }

        Constraints:
            - Only snippets that are public or whose author_id matches the user_id will be included in results.
            - If keywords is empty or only whitespace, returns empty result.
        """
        if not isinstance(keywords, str) or not keywords.strip():
            return {"success": True, "data": []}

        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        keywords_lower = keywords.lower().strip()
        results = []
        for snippet in self.code_snippets.values():
            # Visibility: public or owned by user
            if not (snippet["is_public"] or snippet["author_id"] == user_id):
                continue
            # Content match
            if keywords_lower in snippet["content"].lower():
                results.append(snippet)

        return {"success": True, "data": results}

    def list_public_snippets_by_language(self, language_id: str) -> dict:
        """
        List all public code snippets for the given (supported) programming language.

        Args:
            language_id (str): The ID of the programming language to filter snippets by.

        Returns:
            dict: 
              - {
                    "success": True,
                    "data": List[CodeSnippetInfo], # All matching public snippets (may be empty)
                }
              - {
                    "success": False,
                    "error": str, # Error message if language not found or not supported
                }

        Constraints:
            - Only supported programming languages can be used as filter.
            - Only public code snippets are returned.
        """
        lang = self.programming_languages.get(language_id)
        if not lang:
            return {"success": False, "error": "Programming language not found"}
        if not lang["is_supported"]:
            return {"success": False, "error": "Programming language is not supported"}

        result = [
            snippet for snippet in self.code_snippets.values()
            if snippet["language_id"] == language_id and snippet["is_public"]
        ]
        return {"success": True, "data": result}

    def list_user_snippets(self, user_id: str) -> dict:
        """
        List all code snippets authored by a given user.

        Args:
            user_id (str): The unique ID of the user.

        Returns:
            dict:
                - If user exists:
                    { "success": True, "data": List[CodeSnippetInfo] }
                - If user does not exist:
                    { "success": False, "error": "User does not exist" }

        Constraints:
            - The user must exist in the platform.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
        user_snippets = [
            snippet for snippet in self.code_snippets.values() if snippet["author_id"] == user_id
        ]
        return { "success": True, "data": user_snippets }

    def get_user_by_username(self, username: str) -> dict:
        """
        Retrieve user information given the username.

        Args:
            username (str): The username of the target user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo  # User metadata if found
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (user not found)
            }

        Constraints:
            - Usernames are expected to be unique in the platform.
        """
        for user in self.users.values():
            if user["username"] == username:
                return { "success": True, "data": user }
        return { "success": False, "error": "User not found" }

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user info by user_id.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo  # The user's info if found
            }
            or
            {
                "success": False,
                "error": "User not found"
            }

        Constraints:
            - The user_id must exist in the platform's user records.
        """
        if not user_id or user_id not in self.users:
            return { "success": False, "error": "User not found" }

        return { "success": True, "data": self.users[user_id] }

    def check_snippet_visibility(self, snippet_id: str, user_id: str = None) -> dict:
        """
        Check if a code snippet is public or accessible to a specified user.

        Args:
            snippet_id (str): The ID of the code snippet to check.
            user_id (str, optional): The user to check access for. If None, indicates anonymous/public check.

        Returns:
            dict:
                {
                    "success": True,
                    "visible": bool,  # True if snippet is visible to the user, else False
                }
                or
                {
                    "success": False,
                    "error": str  # Reason for failure, e.g., snippet does not exist, user does not exist
                }

        Constraints:
            - If snippet is public (is_public=True), any user (including None) has access.
            - If snippet is private, only the author has access.
            - If snippet does not exist, return error.
            - If checking private snippet for a user who does not exist, return False (do not error).
        """
        snippet = self.code_snippets.get(snippet_id)
        if snippet is None:
            return {"success": False, "error": "Snippet does not exist"}

        if snippet["is_public"]:
            return {"success": True, "visible": True}

        # Private snippet
        if user_id is None:
            # Anonymous users cannot view private snippets
            return {"success": True, "visible": False}
        if user_id not in self.users:
            # User does not exist; treat as no access (do not error for privacy)
            return {"success": True, "visible": False}
        if snippet["author_id"] == user_id:
            return {"success": True, "visible": True}

        return {"success": True, "visible": False}

    def get_submission_history_for_snippet(self, snippet_id: str) -> dict:
        """
        Retrieve the submission history (edit, execute, etc.) for a given code snippet.

        Args:
            snippet_id (str): The ID of the code snippet to query.

        Returns:
            dict: {
                "success": True,
                "data": List[SubmissionHistoryInfo]  # List may be empty if no history
            }
            or
            {
                "success": False,
                "error": str  # e.g., "Snippet does not exist"
            }

        Constraints:
            - The code snippet identified by snippet_id must exist.
        """
        if snippet_id not in self.code_snippets:
            return { "success": False, "error": "Snippet does not exist" }

        history = [
            info for info in self.submission_history.values()
            if info["snippet_id"] == snippet_id
        ]

        return { "success": True, "data": history }

    def get_snippet_author(self, snippet_id: str) -> dict:
        """
        Get the author_id for a particular code snippet.

        Args:
            snippet_id (str): The unique identifier of the code snippet.

        Returns:
            dict: {
                "success": True,
                "data": { "author_id": str }  # The ID of the author,
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure; e.g., snippet not found
            }

        Constraints:
            - The snippet_id must exist in the platform's code_snippets.
        """
        snippet = self.code_snippets.get(snippet_id)
        if not snippet:
            return { "success": False, "error": "Snippet not found" }
        return { "success": True, "data": { "author_id": snippet["author_id"] } }

    def create_code_snippet(
        self, 
        snippet_id: str,
        content: str, 
        language_id: str, 
        author_id: str, 
        is_public: bool, 
        created_at: str, 
        updated_at: str
    ) -> dict:
        """
        Add a new code snippet to the platform.

        Args:
            snippet_id (str): Unique identifier for the new code snippet.
            content (str): Code content.
            language_id (str): The programming language's ID.
            author_id (str): The user ID of the snippet's creator.
            is_public (bool): Whether the code snippet is public.
            created_at (str): Snippet creation timestamp (ISO string).
            updated_at (str): Snippet last-modified timestamp (ISO string).

        Returns:
            dict: {
                "success": True,
                "message": "Code snippet created successfully"
            }
            OR
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - language_id must exist and be supported.
            - author_id must exist.
            - snippet_id must not already exist.
        """

        # Check if snippet_id is unique
        if snippet_id in self.code_snippets:
            return {"success": False, "error": "A snippet with this ID already exists"}

        # Validate programming language
        if language_id not in self.programming_languages:
            return {"success": False, "error": "Invalid programming language"}
        lang_info = self.programming_languages[language_id]
        if not lang_info.get("is_supported", False):
            return {"success": False, "error": "Programming language is not currently supported"}

        # Validate author
        if author_id not in self.users:
            return {"success": False, "error": "Author does not exist"}

        # Construct snippet
        self.code_snippets[snippet_id] = {
            "snippet_id": snippet_id,
            "content": content,
            "language_id": language_id,
            "author_id": author_id,
            "created_at": created_at,
            "updated_at": updated_at,
            "is_public": is_public
        }

        return {"success": True, "message": "Code snippet created successfully"}

    def edit_code_snippet(
        self,
        snippet_id: str,
        user_id: str,
        new_content: str = None,
        new_language_id: str = None,
        new_visibility: bool = None,
        current_time: str = ""
    ) -> dict:
        """
        Modify the content, language, or visibility of a code snippet,
        only if the user has permission.

        Args:
            snippet_id (str): The ID of the code snippet to edit.
            user_id (str): The ID of the user attempting to edit the snippet.
            new_content (str, optional): New code content (if to be updated).
            new_language_id (str, optional): New programming language ID (if to be updated).
            new_visibility (bool, optional): New visibility (True for public, False for private).
            current_time (str): The new updated_at ISO string (should be current time).

        Returns:
            dict: {
                "success": True,
                "message": "Snippet updated successfully."
            }
            or
            {
                "success": False,
                "error": <error reason>
            }

        Constraints:
            - User must be the author of the code snippet (or have elevated permission).
            - If changing language, the new language must exist and be supported.
            - Must update 'updated_at' timestamp.
            - At least one field (content/language/visibility) must be provided to update.
        """
        # Snippet existence
        snippet = self.code_snippets.get(snippet_id)
        if not snippet:
            return { "success": False, "error": "Code snippet does not exist." }

        # User existence
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User does not exist." }

        # Permissions check (author, or admin)
        if user_id != snippet["author_id"]:
            # Check for elevated permission (simple: account_type == "admin")
            if user.get("account_type", "").lower() != "admin":
                return { "success": False, "error": "Permission denied: cannot edit others' code snippets." }

        # Check at least one update
        if new_content is None and new_language_id is None and new_visibility is None:
            return { "success": False, "error": "No fields to update provided." }

        # Language constraint if updating language
        if new_language_id is not None:
            lang = self.programming_languages.get(new_language_id)
            if not lang:
                return { "success": False, "error": "Programming language does not exist." }
            if not lang.get("is_supported", False):
                return { "success": False, "error": "Programming language is not supported." }

        # Perform updates
        updated = False
        if new_content is not None and new_content != snippet["content"]:
            snippet["content"] = new_content
            updated = True

        if new_language_id is not None and new_language_id != snippet["language_id"]:
            snippet["language_id"] = new_language_id
            updated = True

        if new_visibility is not None and new_visibility != snippet["is_public"]:
            snippet["is_public"] = new_visibility
            updated = True

        if not updated:
            return { "success": False, "error": "No changes detected in provided fields." }

        # Update timestamp
        if current_time:
            snippet["updated_at"] = current_time

        # Save back
        self.code_snippets[snippet_id] = snippet

        return { "success": True, "message": "Snippet updated successfully." }

    def delete_code_snippet(self, snippet_id: str, user_id: str) -> dict:
        """
        Remove a code snippet from the platform, if permitted.
    
        Args:
            snippet_id (str): Unique identifier of the code snippet to remove.
            user_id (str): Unique identifier of the user attempting to perform the deletion.
    
        Returns:
            dict: 
              - Success: {"success": True, "message": "Code snippet deleted."}
              - Failure: {"success": False, "error": <reason>}
    
        Constraints:
            - Code snippet must exist.
            - Only the owner (author_id) or user with privileged account_type ('admin') may delete the snippet.
            - User must exist.
        """
        snippet = self.code_snippets.get(snippet_id)
        if not snippet:
            return {"success": False, "error": "Snippet not found."}

        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User not found."}

        # Allow if author, or user is admin
        is_owner = (snippet["author_id"] == user_id)
        is_admin = (user.get("account_type", "").lower() == "admin")

        if not (is_owner or is_admin):
            return {"success": False, "error": "Permission denied."}

        # Perform deletion
        del self.code_snippets[snippet_id]

        return {"success": True, "message": "Code snippet deleted."}

    def change_snippet_visibility(self, snippet_id: str, user_id: str, is_public: bool) -> dict:
        """
        Set a snippet to public or private. Only allowed if the user is the snippet's author or has admin permissions.
    
        Args:
            snippet_id (str): The id of the code snippet.
            user_id (str): The id of the user requesting the change.
            is_public (bool): The target visibility (True=public, False=private).
        
        Returns:
            dict: {
                "success": True,
                "message": "Snippet visibility updated to public/private."
            }
            or
            {
                "success": False,
                "error": "reason"
            }
        
        Constraints:
            - The snippet must exist.
            - The user must exist.
            - Only the author or admin can change visibility.
        """
        # Check that the snippet exists
        snippet = self.code_snippets.get(snippet_id)
        if snippet is None:
            return {"success": False, "error": "Snippet does not exist"}
    
        # Check that the user exists
        user = self.users.get(user_id)
        if user is None:
            return {"success": False, "error": "User does not exist"}
    
        # Only author or user with admin privileges can change visibility
        is_author = (snippet["author_id"] == user_id)
        is_admin = (user.get("account_type", "").lower() == "admin")
        if not (is_author or is_admin):
            return {"success": False, "error": "Permission denied: only the author or an admin can change visibility"}
    
        # Check if already set
        current_visibility = snippet["is_public"]
        if current_visibility == is_public:
            snippet["updated_at"] = self._next_event_timestamp()
            return {"success": True, "message": f"Snippet visibility is already {'public' if is_public else 'private'}."}
    
        # Perform the update
        snippet["is_public"] = is_public
        snippet["updated_at"] = self._next_event_timestamp()
    
        return {"success": True, "message": f"Snippet visibility updated to {'public' if is_public else 'private'}."}

    def execute_code_snippet(self, snippet_id: str, executor_user_id: str) -> dict:
        """
        Simulate execution of a code snippet and record the result in the submission history.

        Args:
            snippet_id (str): The ID of the code snippet to execute.
            executor_user_id (str): The user ID of the executor.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "message": "Code snippet executed successfully and history recorded.",
                        "result": <execution_result>,
                        "runtime_info": <runtime_information>
                    }
                On failure:
                    {
                        "success": False,
                        "error": <reason>
                    }
        Constraints:
            - Only public snippets or those owned by the executor may be executed.
            - Programming language of the snippet must be supported.
            - Submission history is recorded with unique mission_id.
        """

        # Check that the snippet exists
        snippet = self.code_snippets.get(snippet_id)
        if not snippet:
            return {"success": False, "error": "Snippet does not exist."}
    
        # Check that user exists
        if executor_user_id not in self.users:
            return {"success": False, "error": "Executor user does not exist."}

        # Authorization: snippet must be public or owned by the executor
        if not snippet["is_public"] and snippet["author_id"] != executor_user_id:
            return {"success": False, "error": "Permission denied: Not allowed to execute this private snippet."}

        language_id = snippet["language_id"]
        language_info = self.programming_languages.get(language_id)
        if not language_info:
            return {"success": False, "error": "Programming language not found."}
        if not language_info["is_supported"]:
            return {"success": False, "error": "Programming language is not supported."}

        execution_result, runtime_information = self._infer_execution_outcome(snippet, language_info["name"])
        outcome_is_failure = any(
            marker in execution_result.lower() or marker in runtime_information.lower()
            for marker in ("timeout", "failed", "error", "resource limit exceeded", "crash")
        )

        # Record in submission history
        mission_id = str(uuid.uuid4())
        submission_record = {
            "mission_id": mission_id,
            "snippet_id": snippet_id,
            "user_id": executor_user_id,
            "timestamp": self._next_event_timestamp(),
            "action_type": "executed",
            "result": execution_result,
            "runtime_info": runtime_information
        }
        self.submission_history[mission_id] = submission_record

        if outcome_is_failure:
            return {
                "success": True,
                "message": "Code snippet execution recorded with runtime failure.",
                "result": execution_result,
                "runtime_info": runtime_information
            }

        return {
            "success": True,
            "message": "Code snippet executed successfully and history recorded.",
            "result": execution_result,
            "runtime_info": runtime_information
        }

    def record_submission_history(
        self,
        mission_id: str,
        snippet_id: str,
        user_id: str,
        timestamp: str,
        action_type: str,
        result: str,
        runtime_info: str
    ) -> dict:
        """
        Log an action (create, edit, execute, delete, etc.) for audit/history tracking.

        Args:
            mission_id (str): Unique identifier for this submission history event.
            snippet_id (str): ID of the code snippet concerned.
            user_id (str): Acting user's user_id.
            timestamp (str): ISO or otherwise consistent timestamp for the action.
            action_type (str): Action taken (created, edited, executed, deleted, etc.).
            result (str): Result of the action (text/summary/status).
            runtime_info (str): Additional runtime/environment info if any.

        Returns:
            dict: {
                "success": True,
                "message": "Submission history recorded."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - mission_id must be unique.
            - snippet_id must refer to an existing snippet.
            - user_id must refer to an existing user.
            - action_type should be a valid event string.
        """
        # Enforce mission_id uniqueness
        if mission_id in self.submission_history:
            return {"success": False, "error": "Submission history already exists for this mission_id."}
        # Check snippet exists
        if snippet_id not in self.code_snippets:
            return {"success": False, "error": "Invalid snippet_id (code snippet does not exist)."}
        # Check user exists
        if user_id not in self.users:
            return {"success": False, "error": "Invalid user_id (user does not exist)."}

        # (Optional: Validate action_type)
        valid_action_types = {"created", "edited", "executed", "execute", "deleted", "featured"}
        if action_type not in valid_action_types:
            return {"success": False, "error": f"Invalid action_type '{action_type}'."}

        entry = {
            "mission_id": mission_id,
            "snippet_id": snippet_id,
            "user_id": user_id,
            "timestamp": timestamp,
            "action_type": action_type,
            "result": result,
            "runtime_info": runtime_info
        }
        self.submission_history[mission_id] = entry
        return {"success": True, "message": "Submission history recorded."}

    def add_programming_language(
        self,
        user_id: str,
        language_id: str,
        name: str,
        version: str,
        is_supported: bool
    ) -> dict:
        """
        Add a new supported programming language to the system (admin-level).

        Args:
            user_id (str): The ID of the acting user (must be admin).
            language_id (str): Unique identifier for the programming language.
            name (str): Name of the language.
            version (str): Version string.
            is_supported (bool): Whether this language is currently supported.

        Returns:
            dict: Success or error dict.
                - On success:
                    {
                        "success": True,
                        "message": "Programming language <name> (ID: <language_id>) added."
                    }
                - On failure:
                    {
                        "success": False,
                        "error": "<reason>"
                    }
        Constraints:
            - Only users with 'admin' account_type can add languages.
            - The language_id must not already exist.
            - All fields must be present and valid.
        """
        # Check user exists
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User does not exist."}
        # Check for admin privileges
        if user.get("account_type") != "admin":
            return {"success": False, "error": "Permission denied: admin privileges required."}

        # Check input validity
        if not all([language_id, name, version]):
            return {"success": False, "error": "Missing required programming language information."}

        # Enforce unique language_id
        if language_id in self.programming_languages:
            return {"success": False, "error": "Programming language with this ID already exists."}

        # Create and add language
        self.programming_languages[language_id] = {
            "language_id": language_id,
            "name": name,
            "version": version,
            "is_supported": is_supported
        }

        return {
            "success": True,
            "message": f"Programming language {name} (ID: {language_id}) added."
        }

    def update_programming_language_support(self, language_id: str, is_supported: bool, requester_id: str) -> dict:
        """
        Change the is_supported status of a programming language.
        Only admin users may perform this action.

        Args:
            language_id (str): The id for the programming language to update.
            is_supported (bool): The new support status.
            requester_id (str): The user id performing the operation.

        Returns:
            dict: {
                "success": True,
                "message": str,
            }
            or
            {
                "success": False,
                "error": str,
            }

        Constraints:
            - Only admin users may change programming language support status.
            - language_id must exist.
        """
        # Verify requester exists
        requester = self.users.get(requester_id)
        if not requester:
            return {"success": False, "error": "Requester not found"}
        # Verify admin privileges
        if requester["account_type"] != "admin":
            return {"success": False, "error": "Permission denied (admin required)"}
        # Verify language exists
        lang = self.programming_languages.get(language_id)
        if not lang:
            return {"success": False, "error": "Language not found"}
        # Perform update
        lang["is_supported"] = is_supported
        self.programming_languages[language_id] = lang
        return {
            "success": True,
            "message": f"Support status for language_id {language_id} updated to {is_supported}"
        }


class OnlineCodeCompilerPlatform(BaseEnv):
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

    def get_programming_language_by_name(self, **kwargs):
        return self._call_inner_tool('get_programming_language_by_name', kwargs)

    def list_supported_programming_languages(self, **kwargs):
        return self._call_inner_tool('list_supported_programming_languages', kwargs)

    def get_snippets_by_language(self, **kwargs):
        return self._call_inner_tool('get_snippets_by_language', kwargs)

    def get_snippet_by_id(self, **kwargs):
        return self._call_inner_tool('get_snippet_by_id', kwargs)

    def search_snippets_by_content(self, **kwargs):
        return self._call_inner_tool('search_snippets_by_content', kwargs)

    def list_public_snippets_by_language(self, **kwargs):
        return self._call_inner_tool('list_public_snippets_by_language', kwargs)

    def list_user_snippets(self, **kwargs):
        return self._call_inner_tool('list_user_snippets', kwargs)

    def get_user_by_username(self, **kwargs):
        return self._call_inner_tool('get_user_by_username', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def check_snippet_visibility(self, **kwargs):
        return self._call_inner_tool('check_snippet_visibility', kwargs)

    def get_submission_history_for_snippet(self, **kwargs):
        return self._call_inner_tool('get_submission_history_for_snippet', kwargs)

    def get_snippet_author(self, **kwargs):
        return self._call_inner_tool('get_snippet_author', kwargs)

    def create_code_snippet(self, **kwargs):
        return self._call_inner_tool('create_code_snippet', kwargs)

    def edit_code_snippet(self, **kwargs):
        return self._call_inner_tool('edit_code_snippet', kwargs)

    def delete_code_snippet(self, **kwargs):
        return self._call_inner_tool('delete_code_snippet', kwargs)

    def change_snippet_visibility(self, **kwargs):
        return self._call_inner_tool('change_snippet_visibility', kwargs)

    def execute_code_snippet(self, **kwargs):
        return self._call_inner_tool('execute_code_snippet', kwargs)

    def record_submission_history(self, **kwargs):
        return self._call_inner_tool('record_submission_history', kwargs)

    def add_programming_language(self, **kwargs):
        return self._call_inner_tool('add_programming_language', kwargs)

    def update_programming_language_support(self, **kwargs):
        return self._call_inner_tool('update_programming_language_support', kwargs)
