# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import json
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import uuid
from datetime import datetime
from datetime import timedelta, timezone
import time
from typing import List, Optional



# --- Entity TypedDicts ---

class RepositoryInfo(TypedDict):
    repo_id: str
    name: str
    created_at: str
    owner_id: str
    visibility: str
    collaborators: List[str]  # User IDs with collaborator access

class BranchInfo(TypedDict):
    branch_id: str
    repo_id: str
    name: str
    head_commit_id: str
    is_protected: bool

class CommitInfo(TypedDict):
    commit_id: str
    repo_id: str
    branch_id: str
    author_id: str
    timestamp: str
    parent_commit_ids: List[str]
    message: str
    file_changes: List[str]  # File IDs or descriptors of changes

class FileInfo(TypedDict):
    file_id: str
    repo_id: str
    path: str
    is_binary: bool

class MergeRequestInfo(TypedDict):
    merge_id: str
    repo_id: str
    source_branch_id: str
    target_branch_id: str
    status: str
    conflict_list: List[str]  # List of conflict descriptors (file paths, etc)
    created_at: str
    merged_by: str  # User ID

class UserInfo(TypedDict):
    user_id: str
    username: str
    permissions: List[str]
    email: str
    status: str

# --- Environment Class ---

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Tracks repositories, users, branches, commits, files, and merge requests
        for a collaborative source control system.
        """

        # {repo_id: RepositoryInfo}
        self.repositories: Dict[str, RepositoryInfo] = {}

        # {branch_id: BranchInfo}
        self.branches: Dict[str, BranchInfo] = {}

        # {commit_id: CommitInfo}
        self.commits: Dict[str, CommitInfo] = {}

        # {file_id: FileInfo}
        self.files: Dict[str, FileInfo] = {}

    def _normalize_branch_user_permissions(self) -> Dict[str, Dict[str, List[str]]]:
        raw = getattr(self, "branch_user_permissions", {})
        if isinstance(raw, str):
            text = raw.strip()
            if text.lower() in {"", "{}", "none", "null", '""'}:
                raw = {}
            else:
                try:
                    parsed = json.loads(text)
                    raw = parsed if isinstance(parsed, dict) else {}
                except Exception:
                    raw = {}
        elif not isinstance(raw, dict):
            raw = {}

        normalized: Dict[str, Dict[str, List[str]]] = {}
        for branch_id, user_mapping in raw.items():
            if not isinstance(user_mapping, dict):
                continue
            normalized[branch_id] = {}
            for user_id, permissions in user_mapping.items():
                if permissions is None:
                    normalized[branch_id][user_id] = []
                elif isinstance(permissions, list):
                    normalized[branch_id][user_id] = [str(p) for p in permissions]
                else:
                    normalized[branch_id][user_id] = [str(permissions)]
        self.branch_user_permissions = normalized
        return normalized

    @staticmethod
    def _parse_controlled_datetime(value):
        if not value or not isinstance(value, str):
            return None
        text = value.strip()
        if not text or text.lower() in {"none", "null"}:
            return None
        if text.isdigit():
            return datetime.fromtimestamp(int(text), tz=timezone.utc)
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(text)
        except Exception:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def _next_controlled_timestamp(self) -> datetime:
        explicit = self._parse_controlled_datetime(getattr(self, "current_time", None))
        if explicit is not None:
            return explicit

        seen = []
        for repo in getattr(self, "repositories", {}).values():
            dt = self._parse_controlled_datetime(repo.get("created_at"))
            if dt is not None:
                seen.append(dt)
        for commit in getattr(self, "commits", {}).values():
            dt = self._parse_controlled_datetime(commit.get("timestamp"))
            if dt is not None:
                seen.append(dt)
        for mr in getattr(self, "merge_requests", {}).values():
            for key in ("created_at", "completed_at"):
                dt = self._parse_controlled_datetime(mr.get(key))
                if dt is not None:
                    seen.append(dt)

        if not seen:
            return datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        return max(seen) + timedelta(seconds=1)

    def _next_controlled_timestamp_iso(self) -> str:
        return self._next_controlled_timestamp().isoformat().replace("+00:00", "Z")

        # {merge_id: MergeRequestInfo}
        self.merge_requests: Dict[str, MergeRequestInfo] = {}

        # {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Constraints (to be enforced in logic):
        # - Branch names must be unique within a single repository.
        # - Only users with sufficient permissions can perform merges on protected branches.
        # - Merge can only be completed if there are no unresolved conflicts.
        # - Updates to a repository must maintain commit DAG consistency.
        # - Only existing branches can be merged.
        # - Merge history is tracked for auditing (who, when, what branches).

    def get_repository_by_name(self, repo_name: str) -> dict:
        """
        Retrieve repository details (repo_id, owner_id, visibility, collaborators, etc)
        using the repository's name.

        Args:
            repo_name (str): The name of the repository to search for.

        Returns:
            dict:
                - On success: { "success": True, "data": RepositoryInfo }
                - On failure: { "success": False, "error": str } (if not found)

        Constraints:
            - Repository name should be unique (first match is returned if duplicates exist).
            - No authentication/authorization checks are performed.
        """
        for repo_info in self.repositories.values():
            if repo_info["name"] == repo_name:
                return { "success": True, "data": repo_info }
        return { "success": False, "error": "Repository not found" }

    def list_branches_in_repository(self, repo_id: str) -> dict:
        """
        List all branches’ info for a specified repository.

        Args:
            repo_id (str): The ID of the repository.

        Returns:
            dict: 
              - If repository exists: {"success": True, "data": [BranchInfo, ...]}
              - If not: {"success": False, "error": "Repository not found."}

        Constraints:
            - The repository identified by repo_id must exist.
            - No permission checks are enforced in this operation.
            - If no branches exist in the repository, returns an empty data list.
        """
        if repo_id not in self.repositories:
            return { "success": False, "error": "Repository not found." }

        branches = [
            branch
            for branch in self.branches.values()
            if branch["repo_id"] == repo_id
        ]

        return { "success": True, "data": branches }

    def get_branch_by_name_and_repo(self, repo_id: str, branch_name: str) -> dict:
        """
        Fetch a branch object (BranchInfo) given its name and associated repository ID.

        Args:
            repo_id (str): The unique identifier of the repository.
            branch_name (str): The name of the branch to look up within the repository.

        Returns:
            dict: {
                "success": True,
                "data": BranchInfo,     # On success, the branch information dict
            }
            or
            {
                "success": False,
                "error": str            # On failure, error description
            }

        Constraints:
            - Repository with repo_id must exist.
            - Only branches actually in the given repo are considered.
            - Branch names are unique within a repository (guaranteed).
        """
        if repo_id not in self.repositories:
            return { "success": False, "error": "Repository not found" }

        for branch in self.branches.values():
            if branch["repo_id"] == repo_id and branch["name"] == branch_name:
                return { "success": True, "data": branch }
    
        return { "success": False, "error": "Branch not found in the specified repository" }

    def get_branch_info(self, branch_id: str) -> dict:
        """
        Retrieve details about a branch given its unique branch_id.

        Args:
            branch_id (str): The unique identifier for the branch.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": BranchInfo  # All branch metadata
                    }
                - On failure:
                    {
                        "success": False,
                        "error": "Branch not found"
                    }

        Constraints:
            - branch_id must exist in the system.
        """
        if not branch_id or branch_id not in self.branches:
            return { "success": False, "error": "Branch not found" }

        return { "success": True, "data": self.branches[branch_id] }

    def get_user_by_username(self, username: str) -> dict:
        """
        Retrieve user details given the username.

        Args:
            username (str): The username of the user to retrieve.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "data": UserInfo  # User metadata as a dict
                }
                On failure:
                {
                    "success": False,
                    "error": "User not found"
                }

        Constraints:
            - Usernames are expected to be unique.
        """
        for user in self.users.values():
            if user["username"] == username:
                return { "success": True, "data": user }
        return { "success": False, "error": "User not found" }

    def check_user_merge_permission(self, user_id: str, branch_id: str) -> dict:
        """
        Determine if a user has permission to merge into the target branch.

        Args:
            user_id (str): The ID of the user attempting the merge.
            branch_id (str): The ID of the branch to merge into.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "allowed": bool,
                    "reason": str
                }
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints/Rules:
            - Branch must exist.
            - User must exist.
            - Branch names are unique within a repository.
            - Only users with sufficient permissions can merge into protected branches.
            - For protected: require 'merge_protected' or 'admin' in permissions, or repo owner.
            - For unprotected: must be repo owner or collaborator and user enabled.
        """
        # Validate user existence
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User does not exist" }

        if user.get("status", "").lower() != "active":
            return { "success": True, "data": { "allowed": False, "reason": "User account is not active" } }

        # Validate branch existence
        branch = self.branches.get(branch_id)
        if branch is None:
            return { "success": False, "error": "Branch does not exist" }

        repo_id = branch["repo_id"]
        repo = self.repositories.get(repo_id)
        if repo is None:
            return { "success": False, "error": "Repository for branch does not exist" }

        # Permission checks
        is_repo_owner = (repo["owner_id"] == user_id)
        is_collaborator = user_id in repo["collaborators"]
        user_perms = set(user.get("permissions", []))
        is_protected = branch.get("is_protected", False)
        branch_permissions = set(self._normalize_branch_user_permissions().get(branch_id, {}).get(user_id, []))
    
        if is_protected:
            # Require special permission or ownership
            if is_repo_owner or "merge_protected" in user_perms or "admin" in user_perms or "merge" in branch_permissions:
                return { "success": True, "data": { "allowed": True, "reason": "User has permission to merge into protected branch" } }
            else:
                return { "success": True, "data": { "allowed": False, "reason": "User lacks merge permission for protected branch" } }
        else:
            # Non-protected branch: owner or collaborator
            if is_repo_owner or is_collaborator:
                return { "success": True, "data": { "allowed": True, "reason": "User is owner/collaborator and may merge" } }
            else:
                return { "success": True, "data": { "allowed": False, "reason": "User is not a collaborator or owner" } }

    def list_commits_on_branch(self, branch_id: str) -> dict:
        """
        Retrieve the commit history (all commits) for a given branch.

        Args:
            branch_id (str): The ID of the branch whose commits are to be listed.

        Returns:
            dict: {
                "success": True,
                "data": List[CommitInfo],  # All CommitInfo dicts for this branch, may be empty
            }
            or
            {
                "success": False,
                "error": str,  # Description of the error (e.g., branch not found)
            }

        Constraints:
            - The specified branch must exist in self.branches.
            - No permission checks are enforced for this query.
        """
        if branch_id not in self.branches:
            return { "success": False, "error": "Branch does not exist" }

        commits = [
            commit_info for commit_info in self.commits.values()
            if commit_info["branch_id"] == branch_id
        ]

        # Optionally, sort by timestamp if needed
        commits_sorted = sorted(commits, key=lambda c: c["timestamp"])

        return { "success": True, "data": commits_sorted }

    def get_unresolved_merge_conflicts(self, merge_id: str) -> dict:
        """
        Return the list of unresolved merge conflicts for a merge request, if any.

        Args:
            merge_id (str): The unique identifier for the merge request.

        Returns:
            dict: {
                "success": True,
                "data": List[str],  # List of unresolved conflict descriptors (paths, etc.) (may be empty)
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - merge_id must correspond to an existing merge request.
        """
        if merge_id not in self.merge_requests:
            return {"success": False, "error": "Merge request not found"}

        merge_request = self.merge_requests[merge_id]
        conflict_list = merge_request.get("conflict_list", [])

        return {
            "success": True,
            "data": conflict_list
        }

    def get_merge_requests_for_branches(self, source_branch_id: str, target_branch_id: str) -> dict:
        """
        Retrieve all merge requests involving the specified source and target branches.

        Args:
            source_branch_id (str): The branch ID of the source branch.
            target_branch_id (str): The branch ID of the target branch.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[MergeRequestInfo],  # May be empty if no such merge requests exist.
                }
                or
                {
                    "success": False,
                    "error": str,  # Description of the error (e.g., branch does not exist),
                }

        Constraints:
            - Both source and target branch IDs must refer to existing branches.
        """
        if source_branch_id not in self.branches:
            return { "success": False, "error": "Source branch does not exist" }
        if target_branch_id not in self.branches:
            return { "success": False, "error": "Target branch does not exist" }

        matching_merge_requests = [
            mr for mr in self.merge_requests.values()
            if mr['source_branch_id'] == source_branch_id and mr['target_branch_id'] == target_branch_id
        ]

        return { "success": True, "data": matching_merge_requests }

    def get_merge_history(self, repo_id: str) -> dict:
        """
        Retrieve the audit history of merges for the specified repository.
        Each entry includes: who performed the merge (user_id and optionally username), when (timestamp), and what branches (source and target, with IDs and names).

        Args:
            repo_id (str): The repository ID to query.

        Returns:
            dict:
                success: True, data: [ { source_branch_id, source_branch_name, target_branch_id, target_branch_name, merged_by, merged_by_username, created_at } ... ]
                OR
                success: False, error: "Repository not found"
        Constraints:
            - Repository must exist.
            - Results include only merges with status indicating completion (e.g., "merged").
            - If there are no merge history entries, result is data: [].
        """
        if repo_id not in self.repositories:
            return { "success": False, "error": "Repository not found" }

        # Only consider merge requests for this repo that are completed/merged
        history = []
        for mr in self.merge_requests.values():
            if mr["repo_id"] != repo_id:
                continue
            if mr["status"] not in ("merged", "completed"):  # Only completed merges
                continue

            source_branch_name = ""
            target_branch_name = ""
            if mr["source_branch_id"] in self.branches:
                source_branch_name = self.branches[mr["source_branch_id"]]["name"]
            if mr["target_branch_id"] in self.branches:
                target_branch_name = self.branches[mr["target_branch_id"]]["name"]

            merged_by_username = ""
            if mr.get("merged_by") and mr["merged_by"] in self.users:
                merged_by_username = self.users[mr["merged_by"]]["username"]

            history.append({
                "source_branch_id": mr["source_branch_id"],
                "source_branch_name": source_branch_name,
                "target_branch_id": mr["target_branch_id"],
                "target_branch_name": target_branch_name,
                "merged_by": mr.get("merged_by", ""),
                "merged_by_username": merged_by_username,
                "created_at": mr.get("created_at", "")
            })

        return { "success": True, "data": history }

    def get_commit_info(self, commit_id: str) -> dict:
        """
        Retrieve comprehensive metadata about a specific commit, including message, author, parent commits, and files changed.

        Args:
            commit_id (str): The unique identifier of the commit to query.

        Returns:
            dict: {
                "success": True,
                "data": CommitInfo,   # All fields for this commit
            }
            or
            {
                "success": False,
                "error": str  # error message indicating why (e.g., not found)
            }

        Constraints:
            - The commit must exist in the system.
        """
        commit_info = self.commits.get(commit_id)
        if not commit_info:
            return { "success": False, "error": "Commit does not exist" }
        return { "success": True, "data": commit_info }

    def list_files_in_commit(self, commit_id: str) -> dict:
        """
        List all file information (file_id and path) for files changed in the specified commit.

        Args:
            commit_id (str): The unique identifier for the commit.

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "data": List[Dict[str, str]]
                        # Each dict includes at least 'file_id' and 'path'
                }
                On error: {
                    "success": False,
                    "error": str  # Reason the query failed
                }

        Constraints:
            - The commit must exist in the system.
        """
        if commit_id not in self.commits:
            return {"success": False, "error": "Commit does not exist."}

        commit = self.commits[commit_id]
        changed_file_ids = commit.get("file_changes", [])
        files_info = []

        for fid in changed_file_ids:
            file_info = self.files.get(fid)
            if file_info:
                files_info.append({
                    "file_id": file_info["file_id"],
                    "path": file_info["path"]
                })
            else:
                # Optionally, could include missing files with a warning, 
                # but generally skip inconsistent file refs
                continue

        return {"success": True, "data": files_info}

    def create_merge_request(
        self,
        repo_id: str,
        source_branch_id: str,
        target_branch_id: str,
        created_by_user_id: str
    ) -> dict:
        """
        Create a merge request between a source branch and a target branch within the given repository.
        Initializes status and sets up conflict check (conflict_list may be empty or stubbed).
    
        Args:
            repo_id (str): ID of the repository.
            source_branch_id (str): ID of the source branch to merge from.
            target_branch_id (str): ID of the target branch to merge into.
            created_by_user_id (str): ID of the user creating the merge request.
        
        Returns:
            dict: On success:
                      {
                          "success": True,
                          "message": "Merge request created",
                          "merge_request": MergeRequestInfo
                      }
                  On failure:
                      {
                          "success": False,
                          "error": str
                      }
        
        Constraints:
            - Both branches must exist and belong to the repo.
            - Source and target branch must not be the same.
            - User must exist.
            - There may not be a pending merge request between the same source and target (for simplicity).
        """
        # Check branches exist
        source_branch = self.branches.get(source_branch_id)
        target_branch = self.branches.get(target_branch_id)
        if source_branch is None or target_branch is None:
            return {"success": False, "error": "Source or target branch does not exist."}

        # Check branches belong to repo
        if source_branch["repo_id"] != repo_id or target_branch["repo_id"] != repo_id:
            return {"success": False, "error": "Both branches must belong to the specified repository."}

        # Check source and target are different
        if source_branch_id == target_branch_id:
            return {"success": False, "error": "Source and target branches must be different."}

        # Check repo exists
        if repo_id not in self.repositories:
            return {"success": False, "error": "Repository does not exist."}

        # Check user exists
        if created_by_user_id not in self.users:
            return {"success": False, "error": "User does not exist."}

        # Check for existing open merge request between these branches
        for mr in self.merge_requests.values():
            if (
                mr["repo_id"] == repo_id
                and mr["source_branch_id"] == source_branch_id
                and mr["target_branch_id"] == target_branch_id
                and mr["status"] in ("open", "pending")
            ):
                return {"success": False, "error": "An open merge request already exists between these branches."}

        # Simulate conflict detection (empty conflict_list for now)
        conflict_list = []

        # Generate unique merge_id
        merge_id = str(uuid.uuid4())

        # Use a controlled virtual timestamp rather than host clock time.
        created_at = self._next_controlled_timestamp_iso()

        merge_request: MergeRequestInfo = {
            "merge_id": merge_id,
            "repo_id": repo_id,
            "source_branch_id": source_branch_id,
            "target_branch_id": target_branch_id,
            "status": "open",
            "conflict_list": conflict_list,
            "created_at": created_at,
            "merged_by": ""  # No one yet, just created
        }

        self.merge_requests[merge_id] = merge_request

        return {
            "success": True,
            "message": "Merge request created",
            "merge_request": merge_request
        }

    def resolve_merge_conflict(self, merge_id: str, conflict_descriptor: str) -> dict:
        """
        Mark a specific merge conflict as resolved for a given merge request.

        Args:
            merge_id (str): The ID of the merge request.
            conflict_descriptor (str): The descriptor of the specific conflict to resolve
                                       (e.g., file path).

        Returns:
            dict: On success:
                {
                    "success": True,
                    "message": "Conflict '<conflict_descriptor>' resolved for merge request '<merge_id>'."
                }
            On failure:
                {
                    "success": False,
                    "error": "reason for failure"
                }

        Constraints:
            - The specified merge request must exist.
            - The conflict must be present in the merge request's conflict_list.
        """
        merge_req = self.merge_requests.get(merge_id)
        if merge_req is None:
            return {"success": False, "error": f"Merge request '{merge_id}' does not exist."}

        if conflict_descriptor not in merge_req["conflict_list"]:
            return {"success": False, "error": f"Conflict '{conflict_descriptor}' is not present in merge request '{merge_id}'."}

        # Remove conflict from conflict_list
        merge_req["conflict_list"].remove(conflict_descriptor)

        return {
            "success": True,
            "message": f"Conflict '{conflict_descriptor}' resolved for merge request '{merge_id}'."
        }

    def complete_merge_request(self, merge_id: str, user_id: str) -> dict:
        """
        Finalize a merge request: If all conflicts are resolved and the user has
        permission, perform the merge, update the target branch head, commit DAG,
        and mark the merge status as completed.

        Args:
            merge_id (str): The ID of the merge request.
            user_id (str): The ID of the user completing the merge.

        Returns:
            dict: { "success": True, "message": "..."}
                   or { "success": False, "error": "..." }

        Constraints:
            - Only users with sufficient permissions can merge into protected branches.
            - Merge can only complete if there are no unresolved conflicts.
            - Only existing branches can be merged.
            - Merge history must be updated (merge_request.merge_by, etc).
        """
        # Validate merge request exists
        merge = self.merge_requests.get(merge_id)
        if not merge:
            return {"success": False, "error": "Merge request does not exist."}

        # Validate status is not already complete/cancelled
        if merge["status"] in ("completed", "cancelled"):
            return {"success": False, "error": f"Merge request status is '{merge['status']}' and cannot be completed."}

        # Validate all conflicts resolved
        if merge["conflict_list"]:
            return {"success": False, "error": "Unresolved conflicts remain; merge cannot be completed."}

        # Validate user exists
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User does not exist."}

        # Validate branches exist
        source_branch = self.branches.get(merge["source_branch_id"])
        target_branch = self.branches.get(merge["target_branch_id"])
        if not source_branch or not target_branch:
            return {"success": False, "error": "Source or target branch does not exist."}

        # If protected, check merge permission
        if target_branch["is_protected"]:
            allowed = False
            # Check for 'admin' or 'merge' (or similar) permissions at user or repo level
            # User permissions at repo level
            repo = self.repositories.get(target_branch["repo_id"])
            if not repo:
                return {"success": False, "error": "Target repository does not exist."}
            user_perms = user.get("permissions", [])
            repo_owner = (repo["owner_id"] == user_id)
            is_collaborator = user_id in repo.get("collaborators", [])
            # Assume 'admin' or 'merge' on repo or branch required
            branch_permissions = set(self._normalize_branch_user_permissions().get(target_branch["branch_id"], {}).get(user_id, []))
            if "admin" in user_perms or "merge" in user_perms or repo_owner or is_collaborator or "merge" in branch_permissions:
                allowed = True
            # Could check finer-grained permissions if modeled
            if not allowed:
                return {"success": False, "error": "User lacks permission to merge into protected branch."}

        # Proceed with merge
        # Simulate creating a merge commit

        new_commit_id = str(uuid.uuid4())
        now = self._next_controlled_timestamp_iso()

        # Collect parent commits: heads of target and source branches
        parent_commit_ids = []
        if source_branch["head_commit_id"]:
            parent_commit_ids.append(source_branch["head_commit_id"])
        if target_branch["head_commit_id"]:
            parent_commit_ids.append(target_branch["head_commit_id"])

        # Create the new commit info
        commit_info = {
            "commit_id": new_commit_id,
            "repo_id": target_branch["repo_id"],
            "branch_id": target_branch["branch_id"],
            "author_id": user_id,
            "timestamp": now,
            "parent_commit_ids": parent_commit_ids,
            "message": f"Merge branch '{source_branch['name']}' into '{target_branch['name']}'",
            "file_changes": []  # In a real system, would be the merge diff
        }
        self.commits[new_commit_id] = commit_info

        # Update the target branch's head to the new commit
        target_branch["head_commit_id"] = new_commit_id

        # Update the merge request
        merge["status"] = "completed"
        merge["merged_by"] = user_id

        # Optionally: log merge event (create history/audit entry)
        # Could be implemented as a .log_merge_event(...), but for now just pass (spec may require more).

        return {
            "success": True,
            "message": f"Merge request '{merge_id}' completed. Target branch '{target_branch['name']}' updated."
        }

    def update_branch_head_commit(self, branch_id: str, new_commit_id: str) -> dict:
        """
        Update the head commit pointer of a branch to a new commit (e.g., after completing a merge).

        Args:
            branch_id (str): The ID of the branch to update.
            new_commit_id (str): The commit ID to set as the new head.

        Returns:
            dict: {
                "success": True,
                "message": "Branch head updated successfully."
            }
            or
            {
                "success": False,
                "error": "...reason..."
            }

        Constraints:
            - Branch must exist.
            - Commit must exist.
            - Commit's repo_id must match the branch's repo_id.
            - DAG consistency should be maintained. (This implementation at least checks repo_id match.)
        """
        # 1. Check if branch exists
        branch = self.branches.get(branch_id)
        if not branch:
            return { "success": False, "error": "Branch does not exist." }

        # 2. Check if commit exists
        commit = self.commits.get(new_commit_id)
        if not commit:
            return { "success": False, "error": "Commit does not exist." }

        # 3. Check commit belongs to the same repository as the branch
        if commit["repo_id"] != branch["repo_id"]:
            return { "success": False, "error": "Commit does not belong to the same repository as the branch." }

        # Optionally: Could check if the commit is reachable from the branch history,
        # but for simplicity, just ensure same repo (per state space definition).

        # 4. Update the branch's head_commit_id
        branch["head_commit_id"] = new_commit_id

        return { "success": True, "message": "Branch head updated successfully." }

    def log_merge_event(self, merge_id: str, merged_by: str, completed_at: str) -> dict:
        """
        Record/audit merge completion details.
    
        Args:
            merge_id (str): ID of the merge operation to be logged.
            merged_by (str): User ID who completed the merge.
            completed_at (str): Timestamp when merge was completed (ISO8601/repo format).
    
        Returns:
            dict: {
                "success": True,
                "message": "Merge event logged successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - The merge request must exist.
            - The user must exist.
            - The merge request status must not already be "merged".
            - There must be no unresolved conflicts.
            - All actions are audit-logged in the merge request record.
        """
        merge_req = self.merge_requests.get(merge_id)
        if not merge_req:
            return {"success": False, "error": "Merge request not found."}

        user = self.users.get(merged_by)
        if not user:
            return {"success": False, "error": "User not found."}

        if merge_req.get("status", "").lower() == "merged":
            return {"success": False, "error": "Merge has already been completed."}

        if merge_req.get("conflict_list"):
            if len(merge_req["conflict_list"]) > 0:
                return {"success": False, "error": "Unresolved conflicts remain. Merge cannot be logged as completed."}

        # Update the merge request info to record the auditing
        merge_req["status"] = "merged"
        merge_req["merged_by"] = merged_by
        merge_req["completed_at"] = completed_at  # Even if not present in the schema, audit trailing

        self.merge_requests[merge_id] = merge_req  # Redundant but explicit

        return {"success": True, "message": "Merge event logged successfully."}


    def add_commit_to_branch(
        self,
        repo_id: str,
        branch_id: str,
        author_id: str,
        message: str,
        file_changes: List[str],
        parent_commit_ids: Optional[List[str]] = None
    ) -> dict:
        """
        Add a new commit to a specified branch.

        Args:
            repo_id (str): Repository in which to add the commit.
            branch_id (str): The branch to add the commit to.
            author_id (str): User ID of the commit's author.
            message (str): Commit message.
            file_changes (List[str]): IDs or descriptions of files changed in this commit.
            parent_commit_ids (List[str], optional): Commit IDs of the parent(s). If omitted, uses branch's current head (if any) as single parent.

        Returns:
            dict: 
                On success:
                    { "success": True, "message": "Commit <commit_id> added to branch <branch_id>" }
                On failure:
                    { "success": False, "error": <reason> }

        Constraints:
            - repo_id, branch_id, author_id must all be valid.
            - branch must belong to repo.
            - parent_commit_ids (if given) must exist and belong to the same branch/repo.
            - Updates branch head to this new commit.
        """
        # Validate repository
        if repo_id not in self.repositories:
            return {"success": False, "error": "Repository not found."}

        # Validate branch
        branch = self.branches.get(branch_id)
        if not branch or branch["repo_id"] != repo_id:
            return {"success": False, "error": "Branch not found in the repository."}

        # Validate author
        if author_id not in self.users:
            return {"success": False, "error": "Author (user) not found."}

        # Determine parent commits
        if parent_commit_ids is not None and parent_commit_ids:
            # Explicit parent(s) provided, check their existence and belonging
            for parent_id in parent_commit_ids:
                parent = self.commits.get(parent_id)
                if not parent or parent["branch_id"] != branch_id or parent["repo_id"] != repo_id:
                    return {"success": False, "error": f"Parent commit {parent_id} does not exist in the branch."}
            parents = parent_commit_ids
        else:
            # No parent ids: use current head (if any) or empty (for branch creation)
            current_head = branch.get("head_commit_id")
            if current_head:
                parents = [current_head]
            else:
                parents = []

        # Use a controlled virtual timestamp rather than host clock time.
        timestamp = self._next_controlled_timestamp_iso()

        # Generate a unique commit_id
        commit_id = str(uuid.uuid4())

        # Build commit record
        commit_info = {
            "commit_id": commit_id,
            "repo_id": repo_id,
            "branch_id": branch_id,
            "author_id": author_id,
            "timestamp": timestamp,
            "parent_commit_ids": parents,
            "message": message,
            "file_changes": file_changes,
        }

        # Add commit
        self.commits[commit_id] = commit_info

        # Update branch head_commit_id
        self.branches[branch_id]["head_commit_id"] = commit_id

        return {
            "success": True,
            "message": f"Commit {commit_id} added to branch {branch_id}"
        }


    def create_branch(
        self,
        repo_id: str,
        name: str,
        head_commit_id: str,
        is_protected: bool
    ) -> dict:
        """
        Create a new branch in the specified repository.
    
        Args:
            repo_id (str): The ID of the repository within which to create the branch.
            name (str): The desired branch name (must be unique within the repo).
            head_commit_id (str): The commit which will be the initial HEAD of the branch (must exist in repo).
            is_protected (bool): Whether the branch is protected.

        Returns:
            dict: {
                "success": True,
                "message": "Branch '<name>' created successfully in repository '<repo_id>'."
            }
            or {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Branch names must be unique in the repository.
            - The repository and head commit must exist.
        """
        # Verify repository exists
        if repo_id not in self.repositories:
            return { "success": False, "error": "Repository not found." }

        # Enforce branch name uniqueness within repository
        for branch in self.branches.values():
            if branch["repo_id"] == repo_id and branch["name"] == name:
                return { "success": False, "error": f"Branch name '{name}' already exists in repository." }

        # Check head_commit_id is valid and belongs to repo
        if head_commit_id not in self.commits or self.commits[head_commit_id]["repo_id"] != repo_id:
            return { "success": False, "error": "Invalid head commit id for this repository." }

        # Generate unique branch_id
        branch_id = str(uuid.uuid4())

        branch_info = {
            "branch_id": branch_id,
            "repo_id": repo_id,
            "name": name,
            "head_commit_id": head_commit_id,
            "is_protected": is_protected
        }

        self.branches[branch_id] = branch_info

        return {
            "success": True,
            "message": f"Branch '{name}' created successfully in repository '{repo_id}'.",
            "branch": branch_info
        }

    def delete_branch(self, repo_id: str, branch_name: str) -> dict:
        """
        Delete an existing branch from a repository.

        Args:
            repo_id (str): The ID of the repository from which the branch will be deleted.
            branch_name (str): The name of the branch to delete.

        Returns:
            dict: On success:
                { "success": True, "message": "Branch '<branch_name>' deleted from repository '<repo_id>'." }
            On failure:
                { "success": False, "error": <reason> }
    
        Constraints:
            - Branch must exist in the repository (identified by repo_id and branch_name).
            - Cannot delete protected branches.
            - Branch name uniqueness is preserved by removing it.
    
        Notes:
            - This operation does not delete commits, only the branch pointer.
            - Merge requests referencing this branch are not updated here.
        """
        # Find the branch_id for the branch with this name in this repo
        branch_id = None
        for b_id, branch in self.branches.items():
            if branch["repo_id"] == repo_id and branch["name"] == branch_name:
                branch_id = b_id
                break

        if branch_id is None:
            return { "success": False, "error": "Branch does not exist in repository" }

        branch_info = self.branches[branch_id]

        if branch_info.get("is_protected", False):
            return { "success": False, "error": "Cannot delete protected branch" }

        # Remove branch
        del self.branches[branch_id]

        return {
            "success": True,
            "message": f"Branch '{branch_name}' deleted from repository '{repo_id}'."
        }

    def update_repository_metadata(
        self,
        repo_id: str,
        name: str = None,
        visibility: str = None,
        collaborators: list = None
    ) -> dict:
        """
        Change repository-level metadata such as 'name', 'visibility', and 'collaborators'.

        Args:
            repo_id (str): The repository to modify.
            name (str, optional): New name for the repository.
            visibility (str, optional): New visibility ("public" or "private").
            collaborators (list, optional): List of user IDs to set as collaborators.

        Returns:
            dict: {
                "success": True, "message": "Repository metadata updated."
            }
            or
            {
                "success": False, "error": "reason"
            }

        Constraints:
            - Repository must exist.
            - Visibility (if set) must be 'public' or 'private'.
            - Collaborators (if set) must all be existing user IDs.
            - At least one updatable field must be provided.
        """
        # Check repo exists
        repo = self.repositories.get(repo_id)
        if not repo:
            return { "success": False, "error": "Repository does not exist" }

        if name is None and visibility is None and collaborators is None:
            return { "success": False, "error": "No metadata fields to update provided" }

        # Update name if given (no uniqueness requirement specified)
        if name is not None:
            repo["name"] = name

        # Visibility restricted values
        if visibility is not None:
            if visibility not in ("public", "private"):
                return { "success": False, "error": "Invalid visibility value. Must be 'public' or 'private'." }
            repo["visibility"] = visibility

        # Validate collaborators if given
        if collaborators is not None:
            if not isinstance(collaborators, list):
                return { "success": False, "error": "Collaborators must be provided as a list of user IDs." }
            invalid_users = [uid for uid in collaborators if uid not in self.users]
            if invalid_users:
                return {
                    "success": False,
                    "error": f"The following user IDs do not exist: {invalid_users}"
                }
            repo["collaborators"] = collaborators

        # Write back change (TypedDict is mutable)
        self.repositories[repo_id] = repo
        return { "success": True, "message": "Repository metadata updated." }

    def add_user_permission_to_branch(self, branch_id: str, user_id: str, permission: str) -> dict:
        """
        Grant a user specific permission (e.g., 'merge') on a branch.

        Args:
            branch_id (str): The branch to which permission is to be granted.
            user_id (str): The user to grant permission to.
            permission (str): The permission string to grant (e.g., 'merge').

        Returns:
            dict: {
                "success": True,
                "message": "Permission granted to user on branch."
            }
            OR
            {
                "success": False,
                "error": "<error reason>"
            }

        Constraints:
            - Branch and user must exist.
            - Branch names are unique within repository (implied).
            - Only grant permission if user does not already have it on the branch.
        """
        # Check existence of branch
        if branch_id not in self.branches:
            return { "success": False, "error": "Branch does not exist." }
    
        # Check existence of user
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist." }

        # Create branch_user_permissions structure if not present
        branch_permissions = self._normalize_branch_user_permissions()

        # Set up list for user on that branch if not present
        if branch_id not in branch_permissions:
            branch_permissions[branch_id] = {}

        if user_id not in branch_permissions[branch_id]:
            branch_permissions[branch_id][user_id] = []

        # Check for duplicate
        if permission in branch_permissions[branch_id][user_id]:
            return { "success": False, "error": "User already has this permission on branch." }

        # Grant permission
        branch_permissions[branch_id][user_id].append(permission)
        self.branch_user_permissions = branch_permissions

        return { "success": True, "message": "Permission granted to user on branch." }

    def remove_user_permission_from_branch(self, user_id: str, branch_id: str) -> dict:
        """
        Remove/revoke a user's permission from a specific branch.

        Args:
            user_id (str): The ID of the user to revoke permission from.
            branch_id (str): The ID of the branch.

        Returns:
            dict: 
                - {"success": True, "message": "Permission removed from user on branch."}
                - {"success": False, "error": "<reason>"}

        Constraints:
            - Both user and branch must exist.
            - User must have explicit permission on the target branch (e.g., "branch:{branch_id}" in permissions).
            - No action if the user does not have permission; return an error message.

        Notes:
            - Does not remove repository-level permissions or ownership.
        """
        # Check if user exists
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist."}
        # Check if branch exists
        if branch_id not in self.branches:
            return {"success": False, "error": "Branch does not exist."}

        branch_permissions = self._normalize_branch_user_permissions()
        branch_mapping = branch_permissions.get(branch_id, {})
        if user_id not in branch_mapping or not branch_mapping[user_id]:
            return {"success": False, "error": "User does not have permission on this branch."}

        # This tool revokes the user's explicit branch-level permissions from the target branch.
        del branch_mapping[user_id]
        if not branch_mapping:
            branch_permissions.pop(branch_id, None)
        else:
            branch_permissions[branch_id] = branch_mapping
        self.branch_user_permissions = branch_permissions

        # Keep user-level permission mirrors in sync if a branch token was manually stored there.
        user_info = self.users[user_id]
        permissions_list = user_info.get("permissions", [])
        branch_permission = f"branch:{branch_id}"
        if branch_permission in permissions_list:
            permissions_list.remove(branch_permission)
            user_info["permissions"] = permissions_list
            self.users[user_id] = user_info

        return {"success": True, "message": "Permission removed from user on branch."}

    def rollback_merge(self, merge_id: str) -> dict:
        """
        Revert a merge by undoing the merge commit and restoring the previous
        state of the branch.

        Args:
            merge_id (str): The unique ID of the merge request to roll back.

        Returns:
            dict: {
                "success": True,
                "message": "Merge rollback completed and branch head restored."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Only completed (status == "merged") merge requests may be rolled back.
            - The merge commit must be the current head of the target branch.
            - No further commits must exist on top of the merge commit on the target branch.
            - The branch head will be reset to its parent commit before merge.
            - The merge commit remains in the history for audit purposes, but the branch head moves back.
        """
        # 1. Find the merge request
        merge_req = self.merge_requests.get(merge_id)
        if not merge_req:
            return {"success": False, "error": "Merge request does not exist."}
        if merge_req["status"] != "merged":
            return {"success": False, "error": "Cannot rollback: merge is not completed."}

        target_branch_id = merge_req["target_branch_id"]

        # 2. Get the target branch
        branch = self.branches.get(target_branch_id)
        if not branch:
            return {"success": False, "error": "Target branch does not exist."}

        head_commit_id = branch["head_commit_id"]
        merge_commit = self.commits.get(head_commit_id)
        if not merge_commit:
            return {"success": False, "error": "Current head commit does not exist."}

        # 3. Check if the current head is the merge commit (assume merge commit's 'merged_by' matches merge_req)
        # For traceability, we could store merge_id in commit, but we'll match by timing (latest commit after merge)
        # We check if the commit has multiple parents (a merge)
        if len(merge_commit["parent_commit_ids"]) < 2:
            return {"success": False, "error": "Current branch head is not a merge commit."}

        # 4. Ensure no commits after the merge commit on branch
        # If there are commits whose parent_commit_ids include this merge commit,
        # and are on the same branch, we should prevent rollback.
        for commit in self.commits.values():
            if branch["branch_id"] == commit["branch_id"]:
                if head_commit_id in commit["parent_commit_ids"]:
                    return {"success": False, "error": "Cannot rollback: new commits added after merge."}

        # 5. Rollback: Move branch head to parent (consider first parent as the mainline)
        prev_commit_id = merge_commit["parent_commit_ids"][0]
        # Update branch head
        branch["head_commit_id"] = prev_commit_id

        # Optional: mark the merge_req as "rolled_back" for audit/history (soft delete, do not remove from log)
        merge_req["status"] = "rolled_back"

        # Optional: Log the rollback in audit (not shown, as not in base class)
        return {"success": True, "message": "Merge rollback completed and branch head restored."}


class GitRepositoryManagementSystem(BaseEnv):
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

    def get_repository_by_name(self, **kwargs):
        return self._call_inner_tool('get_repository_by_name', kwargs)

    def list_branches_in_repository(self, **kwargs):
        return self._call_inner_tool('list_branches_in_repository', kwargs)

    def get_branch_by_name_and_repo(self, **kwargs):
        return self._call_inner_tool('get_branch_by_name_and_repo', kwargs)

    def get_branch_info(self, **kwargs):
        return self._call_inner_tool('get_branch_info', kwargs)

    def get_user_by_username(self, **kwargs):
        return self._call_inner_tool('get_user_by_username', kwargs)

    def check_user_merge_permission(self, **kwargs):
        return self._call_inner_tool('check_user_merge_permission', kwargs)

    def list_commits_on_branch(self, **kwargs):
        return self._call_inner_tool('list_commits_on_branch', kwargs)

    def get_unresolved_merge_conflicts(self, **kwargs):
        return self._call_inner_tool('get_unresolved_merge_conflicts', kwargs)

    def get_merge_requests_for_branches(self, **kwargs):
        return self._call_inner_tool('get_merge_requests_for_branches', kwargs)

    def get_merge_history(self, **kwargs):
        return self._call_inner_tool('get_merge_history', kwargs)

    def get_commit_info(self, **kwargs):
        return self._call_inner_tool('get_commit_info', kwargs)

    def list_files_in_commit(self, **kwargs):
        return self._call_inner_tool('list_files_in_commit', kwargs)

    def create_merge_request(self, **kwargs):
        return self._call_inner_tool('create_merge_request', kwargs)

    def resolve_merge_conflict(self, **kwargs):
        return self._call_inner_tool('resolve_merge_conflict', kwargs)

    def complete_merge_request(self, **kwargs):
        return self._call_inner_tool('complete_merge_request', kwargs)

    def update_branch_head_commit(self, **kwargs):
        return self._call_inner_tool('update_branch_head_commit', kwargs)

    def log_merge_event(self, **kwargs):
        return self._call_inner_tool('log_merge_event', kwargs)

    def add_commit_to_branch(self, **kwargs):
        return self._call_inner_tool('add_commit_to_branch', kwargs)

    def create_branch(self, **kwargs):
        return self._call_inner_tool('create_branch', kwargs)

    def delete_branch(self, **kwargs):
        return self._call_inner_tool('delete_branch', kwargs)

    def update_repository_metadata(self, **kwargs):
        return self._call_inner_tool('update_repository_metadata', kwargs)

    def add_user_permission_to_branch(self, **kwargs):
        return self._call_inner_tool('add_user_permission_to_branch', kwargs)

    def remove_user_permission_from_branch(self, **kwargs):
        return self._call_inner_tool('remove_user_permission_from_branch', kwargs)

    def rollback_merge(self, **kwargs):
        return self._call_inner_tool('rollback_merge', kwargs)
