# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import heapq
from datetime import datetime



class RepositoryInfo(TypedDict):
    repository_id: str
    name: str
    description: str
    owner_id: str
    creation_date: str

class BranchInfo(TypedDict):
    branch_name: str
    repository_id: str
    tip_commit_id: str
    creation_date: str
    created_by_user_id: str

class CommitInfo(TypedDict):
    commit_id: str
    parent_commit_ids: List[str]
    author_user_id: str
    timestamp: str
    commit_message: str
    tree_hash: str

class UserInfo(TypedDict):
    user_id: str
    username: str
    permissions: List[str]
    email: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Simulates the state of a Bitbucket Git repository environment.
        """

        # Repositories: {repository_id: RepositoryInfo}
        self.repositories: Dict[str, RepositoryInfo] = {}

        # Branches: {composite_key: BranchInfo}, where composite_key = f"{repository_id}:{branch_name}"
        self.branches: Dict[str, BranchInfo] = {}

        # Commits: {commit_id: CommitInfo}
        self.commits: Dict[str, CommitInfo] = {}

        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Constraints:
        # - Branch names must be unique within a repository.
        # - Only users with appropriate permissions can create branches.
        # - The repository state is updated atomically with each Git operation.
        # - Each new branch must reference an existing commit as its starting point.

    def get_repository_by_name(self, name: str) -> dict:
        """
        Retrieve metadata for a repository with the given name.

        Args:
            name (str): The repository name to search for.

        Returns:
            dict: {
                "success": True,
                "data": RepositoryInfo  # Repository metadata
            }
            or
            {
                "success": False,
                "error": str  # "Repository not found"
            }

        Constraints:
            - The repository name is case-sensitive.
            - Only one repository will be returned (first match if duplicates exist, though names should be unique).
        """
        for repo_info in self.repositories.values():
            if repo_info["name"] == name:
                return { "success": True, "data": repo_info }
        return { "success": False, "error": "Repository not found" }

    def get_repositories_by_owner(self, user_id: str) -> dict:
        """
        List all repositories owned by a specific user.

        Args:
            user_id (str): The ID of the user whose owned repositories to list.

        Returns:
            dict: {
                "success": True,
                "data": List[RepositoryInfo]  # May be empty if user owns none
            }
            or
            {
                "success": False,
                "error": str  # Error description, e.g. user does not exist
            }

        Constraints:
            - The specified user_id must exist.
            - Includes all repositories with owner_id == user_id.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}
        result = [
            repo_info for repo_info in self.repositories.values()
            if repo_info["owner_id"] == user_id
        ]
        return {"success": True, "data": result}

    def get_repository_info(self, repository_id: str) -> dict:
        """
        Retrieve detailed information about a repository given its repository_id.

        Args:
            repository_id (str): The ID of the repository to fetch.

        Returns:
            dict: {
                "success": True,
                "data": RepositoryInfo  # (Dictionary with info about the repository)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g. repository does not exist)
            }

        Constraints:
            - The provided repository_id must exist in the environment.
        """
        repo = self.repositories.get(repository_id)
        if repo is None:
            return {"success": False, "error": "Repository does not exist"}
        return {"success": True, "data": repo}

    def list_branches_in_repository(self, repository_id: str) -> dict:
        """
        List all branch names in a specified repository.

        Args:
            repository_id (str): The unique identifier for the repository.

        Returns:
            dict:
                If repository exists:
                    {
                        "success": True,
                        "data": List[str]  # List of branch names (may be empty)
                    }
                If repository does not exist:
                    {
                        "success": False,
                        "error": "Repository does not exist"
                    }
        Constraints:
            - Repository must exist.
        """
        if repository_id not in self.repositories:
            return { "success": False, "error": "Repository does not exist" }

        # Branches' keys are composite: f"{repository_id}:{branch_name}"
        branches_in_repo = [
            branch_info['branch_name']
            for branch_info in self.branches.values()
            if branch_info['repository_id'] == repository_id
        ]

        return { "success": True, "data": branches_in_repo }

    def branch_exists(self, repository_id: str, branch_name: str) -> dict:
        """
        Check if a branch name already exists in a given repository.

        Args:
            repository_id (str): The ID of the repository in which to check for the branch.
            branch_name (str): The name of the branch to check.

        Returns:
            dict: 
                On success:
                    { "success": True, "exists": bool }
                On failure (repository does not exist):
                    { "success": False, "error": str }

        Constraints:
            - The repository with the provided ID must exist.
            - No permissions required for this query operation.
        """
        if repository_id not in self.repositories:
            return { "success": False, "error": "Repository does not exist" }

        composite_key = f"{repository_id}:{branch_name}"
        exists = composite_key in self.branches

        return { "success": True, "exists": exists }

    def get_branch_info(self, repository_id: str, branch_name: str) -> dict:
        """
        Retrieve detailed info for a specific branch identified by (repository_id, branch_name).

        Args:
            repository_id (str): The unique ID of the repository.
            branch_name (str): The name of the branch within the repository.

        Returns:
            dict: {
                "success": True,
                "data": BranchInfo     # TypedDict containing all branch metadata
            }
            or
            {
                "success": False,
                "error": str           # "Branch not found"
            }

        Constraints:
            - Branch is uniquely identified by (repository_id, branch_name).
            - No permissions are checked for this query.
        """
        branch_key = f"{repository_id}:{branch_name}"
        branch_info = self.branches.get(branch_key)
        if branch_info is None:
            return { "success": False, "error": "Branch not found" }
        return { "success": True, "data": branch_info }

    def list_commits_in_repository(self, repository_id: str, limit: int = None) -> dict:
        """
        List all commits (or the most recent N) in the given repository.

        Args:
            repository_id (str): ID of the repository to search in.
            limit (int, optional): Maximum number of commits to return (sorted by timestamp descending).
                                  If None, returns all.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[CommitInfo]  # Ordered by timestamp descending, may be empty
                    }
                On failure:
                    {
                        "success": False,
                        "error": str
                    }
        Constraints:
            - The repository must exist.
            - If limit is provided, must be a positive integer.
            - A commit is in the repo if it is reachable from any branch tip in that repo.
        """

        if repository_id not in self.repositories:
            return {"success": False, "error": "Repository does not exist"}

        if limit is not None:
            if not isinstance(limit, int) or limit <= 0:
                return {"success": False, "error": "Limit must be a positive integer if provided"}

        # 1. Find all tip commits from all branches in this repo.
        tip_commit_ids = []
        for composite_key, branch in self.branches.items():
            if branch["repository_id"] == repository_id:
                tip_commit_ids.append(branch["tip_commit_id"])

        # 2. Traverse parents recursively to collect all reachable commits.
        reachable_commits = set()
        def collect_commits(commit_id):
            if commit_id not in self.commits or commit_id in reachable_commits:
                return
            reachable_commits.add(commit_id)
            for parent_id in self.commits[commit_id]["parent_commit_ids"]:
                collect_commits(parent_id)

        for tip_id in tip_commit_ids:
            collect_commits(tip_id)

        # 3. Gather and sort commits by timestamp descending (newest first)
        reachable_commit_infos = []
        for commit_id in reachable_commits:
            commit = self.commits.get(commit_id)
            if commit:
                reachable_commit_infos.append(commit)

        # Sorting: timestamps assumed to be ISO strings; convert to datetime for sorting
        reachable_commit_infos.sort(key=lambda c: c["timestamp"], reverse=True)

        if limit is not None:
            reachable_commit_infos = reachable_commit_infos[:limit]

        return {"success": True, "data": reachable_commit_infos}

    def get_commit_info(self, commit_id: str) -> dict:
        """
        Obtain detailed information for a specific commit by commit_id.

        Args:
            commit_id (str): The unique identifier for the commit.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": CommitInfo  # Full info for the commit
                    }
                - If commit_id not found:
                    {
                        "success": False,
                        "error": "Commit not found"
                    }

        Constraints:
            - commit_id must exist in the repository.
        """
        commit_info = self.commits.get(commit_id)
        if not commit_info:
            return { "success": False, "error": "Commit not found" }
        return { "success": True, "data": commit_info }

    def get_repository_default_branch(self, repository_id: str) -> dict:
        """
        Identify the default/main branch for a specified repository.

        Args:
            repository_id (str): The ID of the repository.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": branch_name (str)  # The default branch name
                    }
                On failure:
                    {
                        "success": False,
                        "error": error_message (str)
                    }

        Constraints:
            - The repository must exist.
            - The repository must have a default branch configured.
            - The default branch must exist in the repository.
        """
        # Check if repository exists
        if repository_id not in self.repositories:
            return { "success": False, "error": "Repository does not exist" }

        # Ensure default_branches mapping exists
        if not hasattr(self, "default_branches"):
            self.default_branches = {}

        # Check if a default branch is set
        if repository_id not in self.default_branches:
            return { "success": False, "error": "Default branch not set for this repository" }

        branch_name = self.default_branches[repository_id]
        branch_key = f"{repository_id}:{branch_name}"

        # Check that the default branch exists
        if branch_key not in self.branches:
            return { "success": False, "error": "Default branch does not exist" }

        return { "success": True, "data": branch_name }

    def get_tip_commit_of_branch(self, repository_id: str, branch_name: str) -> dict:
        """
        Retrieve the CommitInfo of the latest (tip) commit for a given branch in a repository.

        Args:
            repository_id (str): The ID of the repository.
            branch_name (str): The name of the branch.

        Returns:
            dict: On success:
                      {
                        "success": True,
                        "data": CommitInfo  # Information about the tip commit
                      }
                  On failure:
                      {
                        "success": False,
                        "error": str  # Description of the error
                      }

        Constraints:
            - The branch must exist in the repository.
            - The tip commit must exist for the branch.
        """
        composite_key = f"{repository_id}:{branch_name}"
        branch_info = self.branches.get(composite_key)
        if not branch_info:
            return { "success": False, "error": "Branch not found in repository." }
        tip_commit_id = branch_info.get("tip_commit_id")
        commit_info = self.commits.get(tip_commit_id)
        if not commit_info:
            return { "success": False, "error": "Tip commit for branch not found." }
        return { "success": True, "data": commit_info }

    def get_user_by_username(self, username: str) -> dict:
        """
        Retrieve user object (user_id, username, permissions, email, etc.) given a username.

        Args:
            username (str): The username to look up.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo  # The matching user's info,
            }
            OR
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Usernames are assumed unique. If not found, reports an error.
        """
        for user in self.users.values():
            if user["username"] == username:
                return { "success": True, "data": user }
        return { "success": False, "error": "User not found" }

    def get_user_permissions_on_repository(self, user_id: str, repository_id: str) -> dict:
        """
        Retrieve the list of permissions a user has on a specific repository.

        Args:
            user_id (str): The ID of the user.
            repository_id (str): The ID of the repository.

        Returns:
            dict:
                { "success": True, "data": List[str] }
                or
                { "success": False, "error": str }

        Constraints:
            - The user must exist.
            - The repository must exist.
            - Returns the permissions list from UserInfo (per-user global permissions).
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
        if repository_id not in self.repositories:
            return { "success": False, "error": "Repository does not exist" }
        user_info = self.users[user_id]
        permissions = user_info.get("permissions", [])
        return { "success": True, "data": permissions }

    def create_branch(
        self,
        repository_id: str,
        branch_name: str,
        tip_commit_id: str,
        created_by_user_id: str,
        creation_date: str
    ) -> dict:
        """
        Create a new branch in the repository, pointing to an existing commit.

        Args:
            repository_id (str): The target repository's unique ID.
            branch_name (str): The branch's unique name within the repo.
            tip_commit_id (str): The commit from which to branch.
            created_by_user_id (str): The user (by user_id) performing the operation.
            creation_date (str): ISO8601 datetime branch creation timestamp.

        Returns:
            dict:
                On success:
                    {"success": True, "message": "Branch <name> created in repository <id>."}
                On failure:
                    {"success": False, "error": <reason>} 

        Constraints:
            - Branch name must be unique in the repository.
            - User must exist and have proper permissions.
            - Repository and commit must exist.
        """
        # Check repository exists
        if repository_id not in self.repositories:
            return { "success": False, "error": "Repository does not exist." }
    
        # Check user exists
        if created_by_user_id not in self.users:
            return { "success": False, "error": "User does not exist." }
    
        # Check commit exists
        if tip_commit_id not in self.commits:
            return { "success": False, "error": "Tip commit does not exist." }
    
        # Check branch name uniqueness in this repository
        composite_key = f"{repository_id}:{branch_name}"
        if composite_key in self.branches:
            return { "success": False, "error": "Branch name already exists in repository." }
    
        # Check user permissions (must have e.g. "create_branch" or "write" or be owner)
        user = self.users[created_by_user_id]
        repo = self.repositories[repository_id]
        user_permissions = user.get("permissions", [])
        is_owner = (repo.get("owner_id") == created_by_user_id)
        if not (is_owner or "create_branch" in user_permissions or "write" in user_permissions or "admin" in user_permissions):
            return { "success": False, "error": "User lacks permission to create branches in this repository." }
    
        # Create the branch
        self.branches[composite_key] = {
            "branch_name": branch_name,
            "repository_id": repository_id,
            "tip_commit_id": tip_commit_id,
            "creation_date": creation_date,
            "created_by_user_id": created_by_user_id
        }
        return {
            "success": True,
            "message": f"Branch {branch_name} created in repository {repository_id}."
        }

    def delete_branch(self, repository_id: str, branch_name: str, user_id: str) -> dict:
        """
        Remove a branch from the repository.

        Args:
            repository_id (str): Target repository.
            branch_name (str): Branch to delete.
            user_id (str): User requesting the operation.

        Returns:
            dict: {
                "success": True,
                "message": str  # Confirmation message
            }
            or
            {
                "success": False,
                "error": str  # Error description
            }

        Constraints:
            - Only users with appropriate permissions ("delete_branch" or "admin") can delete branches.
            - Branch must exist within the specified repository.
            - User and repository must exist.
        """
        composite_key = f"{repository_id}:{branch_name}"

        # Check for repository existence
        if repository_id not in self.repositories:
            return { "success": False, "error": "Repository not found." }

        # Check for user existence
        if user_id not in self.users:
            return { "success": False, "error": "User not found." }

        # Check for branch existence
        if composite_key not in self.branches:
            return { "success": False, "error": "Branch does not exist in the repository." }

        # Permission check
        user_permissions = self.users[user_id].get("permissions", [])
        if not ("admin" in user_permissions or "delete_branch" in user_permissions):
            return { "success": False, "error": "Permission denied." }

        # Perform the delete operation
        del self.branches[composite_key]

        return {
            "success": True,
            "message": f"Branch '{branch_name}' deleted from repository '{repository_id}'."
        }

    def update_branch_tip_commit(
        self,
        repository_id: str,
        branch_name: str,
        new_tip_commit_id: str
    ) -> dict:
        """
        Move the tip (HEAD) of a branch to another commit within the same repository.

        Args:
            repository_id (str): The ID of the repository.
            branch_name (str): The name of the branch to update.
            new_tip_commit_id (str): The commit ID to set as the new tip.

        Returns:
            dict:
                - On success: {"success": True, "message": "Branch tip updated to new commit."}
                - On failure: {"success": False, "error": <reason>}
    
        Constraints:
            - The repository and branch must exist.
            - The new_tip_commit_id must be a valid commit.
            - The update is atomic.
        """
        # Check repository existence
        if repository_id not in self.repositories:
            return {"success": False, "error": "Repository does not exist."}
    
        branch_key = f"{repository_id}:{branch_name}"
        if branch_key not in self.branches:
            return {"success": False, "error": "Branch does not exist in the repository."}
    
        if new_tip_commit_id not in self.commits:
            return {"success": False, "error": "Specified commit does not exist."}
    
        # Update the tip commit_id
        self.branches[branch_key]['tip_commit_id'] = new_tip_commit_id
    
        return {"success": True, "message": "Branch tip updated to new commit."}

    def log_repository_event(
        self,
        repository_id: str,
        branch_name: str,
        user_id: str,
        timestamp: str,
        event_type: str = "branch_creation",
        details: str = None
    ) -> dict:
        """
        Record an event/audit entry for repository branch operations.

        Args:
            repository_id (str): The repository in which the branch operation occurred.
            branch_name (str): The name of the branch involved in the event.
            user_id (str): The ID of the user who performed the operation.
            timestamp (str): Timestamp of the event (ISO 8601 or RFC 3339 string).
            event_type (str, optional): Event category such as 'branch_creation', 'branch_restore',
                'branch_tip_update', or 'branch_deletion'. Defaults to 'branch_creation'.
            details (str, optional): Free-form audit detail text. If omitted, a default detail
                string is generated based on event_type.

        Returns:
            dict:
                - On success: {'success': True, 'message': 'Event logged for branch creation'}
                  or {'success': True, 'message': 'Repository event logged successfully'}
                - On failure: {'success': False, 'error': 'reason'}

        Constraints:
            - The repository_id must reference an existing repository.
            - The branch_name identifies the branch involved in the event; for deletion/cleanup
              logs it may refer to a branch that has already been removed.
            - The user_id must correspond to an existing user.
        """
        # Ensure the event log exists
        if not hasattr(self, "audit_log"):
            self.audit_log = []

        # Check repository exists
        if repository_id not in self.repositories:
            return { "success": False, "error": "Repository does not exist" }

        # Check user exists
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        normalized_event_type = event_type if isinstance(event_type, str) and event_type.strip() else "branch_creation"
        if details is None or (isinstance(details, str) and details.strip() == ""):
            if normalized_event_type == "branch_creation":
                details = f"Branch '{branch_name}' created in repository '{repository_id}' by user '{user_id}' at {timestamp}"
            else:
                details = (
                    f"Repository event '{normalized_event_type}' recorded for branch "
                    f"'{branch_name}' in repository '{repository_id}' by user '{user_id}' at {timestamp}"
                )

        # Event structure
        event = {
            "event_type": normalized_event_type,
            "repository_id": repository_id,
            "branch_name": branch_name,
            "user_id": user_id,
            "timestamp": timestamp,
            "details": details
        }
        self.audit_log.append(event)

        if normalized_event_type == "branch_creation":
            return { "success": True, "message": "Event logged for branch creation" }
        return { "success": True, "message": "Repository event logged successfully" }

    def set_repository_default_branch(self, repository_id: str, branch_name: str) -> dict:
        """
        Designate a branch as the default/main for a repository.

        Args:
            repository_id (str): The ID of the target repository.
            branch_name (str): The branch name to set as default.

        Returns:
            dict: {
                "success": True,
                "message": str
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The repository must exist.
            - The branch must exist within the specified repository.
            - If 'default_branch' field is not present in repository info, it will be added.
        """
        # Check if repository exists
        repo = self.repositories.get(repository_id)
        if not repo:
            return { "success": False, "error": "Repository does not exist" }

        # Check if the branch exists in the repository
        composite_key = f"{repository_id}:{branch_name}"
        if composite_key not in self.branches:
            return { "success": False, "error": "Branch does not exist in the repository" }

        if not hasattr(self, "default_branches") or not isinstance(self.default_branches, dict):
            self.default_branches = {}
        self.default_branches[repository_id] = branch_name
        self.repositories[repository_id]["default_branch"] = branch_name

        return {
            "success": True,
            "message": f"Default branch set to '{branch_name}' for repository '{repository_id}'"
        }


class BitbucketGitRepository(BaseEnv):
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
            copied = copy.deepcopy(value)
            if key == "branches" and isinstance(copied, dict):
                normalized = {}
                for branch_key, branch_info in copied.items():
                    if not isinstance(branch_info, dict):
                        continue
                    repository_id = branch_info.get("repository_id")
                    branch_name = branch_info.get("branch_name")
                    if repository_id and branch_name:
                        normalized[f"{repository_id}:{branch_name}"] = branch_info
                    else:
                        normalized[branch_key] = branch_info
                copied = normalized
            elif key == "default_branches":
                copied = copied if isinstance(copied, dict) else {}
            elif key == "audit_log":
                copied = copied if isinstance(copied, list) else []
            setattr(env, key, copied)

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

    def get_repositories_by_owner(self, **kwargs):
        return self._call_inner_tool('get_repositories_by_owner', kwargs)

    def get_repository_info(self, **kwargs):
        return self._call_inner_tool('get_repository_info', kwargs)

    def list_branches_in_repository(self, **kwargs):
        return self._call_inner_tool('list_branches_in_repository', kwargs)

    def branch_exists(self, **kwargs):
        return self._call_inner_tool('branch_exists', kwargs)

    def get_branch_info(self, **kwargs):
        return self._call_inner_tool('get_branch_info', kwargs)

    def list_commits_in_repository(self, **kwargs):
        return self._call_inner_tool('list_commits_in_repository', kwargs)

    def get_commit_info(self, **kwargs):
        return self._call_inner_tool('get_commit_info', kwargs)

    def get_repository_default_branch(self, **kwargs):
        return self._call_inner_tool('get_repository_default_branch', kwargs)

    def get_tip_commit_of_branch(self, **kwargs):
        return self._call_inner_tool('get_tip_commit_of_branch', kwargs)

    def get_user_by_username(self, **kwargs):
        return self._call_inner_tool('get_user_by_username', kwargs)

    def get_user_permissions_on_repository(self, **kwargs):
        return self._call_inner_tool('get_user_permissions_on_repository', kwargs)

    def create_branch(self, **kwargs):
        return self._call_inner_tool('create_branch', kwargs)

    def delete_branch(self, **kwargs):
        return self._call_inner_tool('delete_branch', kwargs)

    def update_branch_tip_commit(self, **kwargs):
        return self._call_inner_tool('update_branch_tip_commit', kwargs)

    def log_repository_event(self, **kwargs):
        return self._call_inner_tool('log_repository_event', kwargs)

    def set_repository_default_branch(self, **kwargs):
        return self._call_inner_tool('set_repository_default_branch', kwargs)
