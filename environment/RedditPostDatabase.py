# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict



class PostInfo(TypedDict):
    post_id: str
    title: str
    content: str
    author_id: str
    timestamp: str
    subreddit_id: str
    score: int
    num_comments: int
    flair: str
    status: str  # e.g., active, deleted, archived

class AuthorInfo(TypedDict):
    author_id: str
    username: str
    account_sta: str

class SubredditInfo(TypedDict):
    subreddit_id: str
    subreddit_name: str
    description: str
    creation_date: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for managing Reddit posts, authors, and subreddits.
        """

        # Posts: {post_id: PostInfo}
        self.posts: Dict[str, PostInfo] = {}

        # Authors: {author_id: AuthorInfo}
        self.authors: Dict[str, AuthorInfo] = {}

        # Subreddits: {subreddit_id: SubredditInfo}
        self.subreddits: Dict[str, SubredditInfo] = {}

        # Constraints:
        # - Each post must have a unique post_id.
        # - Posts may only be updated or deleted according to their status (e.g., archived posts may be immutable).
        # - Every post must be associated with a valid author and subreddit.
        # - Post content and metadata must be retrievable by post_id.

    def get_post_by_id(self, post_id: str) -> dict:
        """
        Retrieve the full metadata and content of a post given its unique post_id.

        Args:
            post_id (str): The unique identifier of the post.

        Returns:
            dict:
                - If found: {"success": True, "data": PostInfo}
                - If not found: {"success": False, "error": "Post with id <post_id> does not exist"}

        Constraints:
            - The post_id must exist in the database.
            - Returns all metadata and content for the post.
        """
        post = self.posts.get(post_id)
        if not post:
            return {"success": False, "error": f"Post with id {post_id} does not exist"}
        return {"success": True, "data": post}

    def get_multiple_posts_by_ids(self, post_ids: list[str]) -> dict:
        """
        Retrieve details (full metadata/content) for a batch of posts given a list of post_ids.

        Args:
            post_ids (list[str]): List of post IDs to query.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[PostInfo],  # List of posts found (order may match input or be unordered)
                    "not_found": List[str]   # post_ids from input not present in the database
                }
            If `post_ids` is empty, returns empty data and not_found lists.
        """
        found_posts = []
        not_found = []
        for pid in post_ids:
            post = self.posts.get(pid)
            if post:
                found_posts.append(post)
            else:
                not_found.append(pid)
        return {
            "success": True,
            "data": found_posts,
            "not_found": not_found
        }

    def list_posts_by_author(self, author_id: str) -> dict:
        """
        Retrieve all post records authored by the specified author_id.

        Args:
            author_id (str): The ID of the author.

        Returns:
            dict:
                - success: True and 'data' is a list of PostInfo objects representing posts by this author
                - success: False and 'error' describes the error if the author does not exist

        Constraints:
            - author_id must exist in the authors database.
            - returns an empty list if author exists but has no posts.
        """
        if author_id not in self.authors:
            return { "success": False, "error": "Author does not exist" }

        result = [
            post_info for post_info in self.posts.values()
            if post_info["author_id"] == author_id
        ]
        return { "success": True, "data": result }

    def list_posts_by_subreddit(self, subreddit_id: str) -> dict:
        """
        Retrieve all posts belonging to the given subreddit_id.

        Args:
            subreddit_id (str): The unique identifier of the subreddit.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[PostInfo],   # array of post records, possibly empty
                }
                or
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - subreddit_id must exist in the environment.
            - Each result is a full PostInfo dict for posts with matching subreddit_id.
        """
        if subreddit_id not in self.subreddits:
            return { "success": False, "error": "Subreddit does not exist" }
    
        posts = [
            post for post in self.posts.values()
            if post["subreddit_id"] == subreddit_id
        ]

        return { "success": True, "data": posts }

    def get_author_by_id(self, author_id: str) -> dict:
        """
        Retrieve the details of an author using their author_id.

        Args:
            author_id (str): The unique identifier for the author.

        Returns:
            dict: 
                On success: { "success": True, "data": AuthorInfo }
                On failure: { "success": False, "error": "Author not found" }

        Constraints:
            - The given author_id must exist in the authors database.
        """
        author_info = self.authors.get(author_id)
        if author_info is None:
            return { "success": False, "error": "Author not found" }
        return { "success": True, "data": author_info }

    def get_subreddit_by_id(self, subreddit_id: str) -> dict:
        """
        Retrieve the details of a subreddit by subreddit_id.

        Args:
            subreddit_id (str): The unique identifier for the subreddit.

        Returns:
            dict: On success:
                      {"success": True, "data": SubredditInfo}
                  On failure:
                      {"success": False, "error": "Subreddit not found"}

        Constraints:
            - subreddit_id must exist in the subreddit database.
        """
        if subreddit_id not in self.subreddits:
            return {"success": False, "error": "Subreddit not found"}
        return {"success": True, "data": self.subreddits[subreddit_id]}

    def filter_posts_by_status(self, status: str) -> dict:
        """
        List all posts with the given status.

        Args:
            status (str): The status value to filter posts by (e.g., 'active', 'deleted', 'archived').

        Returns:
            dict: On success:
                {
                    "success": True,
                    "data": List[PostInfo]  # List of posts matching the status (may be empty)
                }
                On error:
                {
                    "success": False,
                    "error": str  # Reason for failure
                }
        Constraints:
            - Only filters posts by the 'status' field, does not modify state.
            - Returns all posts where post['status'] == status.
        """
        if status is None:
            return { "success": False, "error": "Status parameter must be provided" }

        matching_posts = [
            post for post in self.posts.values()
            if post.get("status") == status
        ]

        return { "success": True, "data": matching_posts }

    def filter_posts_by_flair(self, flair: str) -> dict:
        """
        Search for posts with a specific flair.

        Args:
            flair (str): The flair string to filter posts by.

        Returns:
            dict: {
                "success": True,
                "data": List[PostInfo]  # List of posts whose 'flair' matches the given flair, may be empty
            }

        Notes:
            - If no posts have the given flair, returns an empty list (successfully).
            - Flair-match is exact (case-sensitive).
        """
        result = [post for post in self.posts.values() if post.get("flair") == flair]
        return { "success": True, "data": result }

    def get_post_metadata(self, post_id: str) -> dict:
        """
        Retrieve only the basic metadata (title, author, timestamp, subreddit) for the given post_id.

        Args:
            post_id (str): Unique identifier of the post.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "title": str,
                    "author_id": str,
                    "timestamp": str,
                    "subreddit_id": str
                }
            }
            or
            {
                "success": False,
                "error": str  # e.g., "Post not found"
            }

        Constraints:
            - The post_id must exist in the database.
        """
        post = self.posts.get(post_id)
        if not post:
            return { "success": False, "error": "Post not found" }

        metadata = {
            "title": post["title"],
            "author_id": post["author_id"],
            "timestamp": post["timestamp"],
            "subreddit_id": post["subreddit_id"]
        }
        return { "success": True, "data": metadata }

    def create_post(
        self,
        post_id: str,
        title: str,
        content: str,
        author_id: str,
        timestamp: str,
        subreddit_id: str,
        flair: str = "",
        status: str = "active"
    ) -> dict:
        """
        Add a new post to the database.

        Args:
            post_id (str): Unique identifier for the post.
            title (str): Post title.
            content (str): Post body/content.
            author_id (str): Author's unique ID (must exist).
            timestamp (str): Timestamp of creation (ISO or unix time).
            subreddit_id (str): Subreddit identifier (must exist).
            flair (str, optional): Flair for the post. Default "".
            status (str, optional): Post status. Default "active".

        Returns:
            dict: {
                "success": True,
                "message": "Post created successfully"
            } or {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - post_id must be unique.
            - author_id must exist in authors.
            - subreddit_id must exist in subreddits.
        """
        # Uniqueness check
        if post_id in self.posts:
            return { "success": False, "error": "Post ID already exists" }

        # Author existence check
        if author_id not in self.authors:
            return { "success": False, "error": "Author does not exist" }

        # Subreddit existence check
        if subreddit_id not in self.subreddits:
            return { "success": False, "error": "Subreddit does not exist" }

        # Compose PostInfo
        post_info: PostInfo = {
            "post_id": post_id,
            "title": title,
            "content": content,
            "author_id": author_id,
            "timestamp": timestamp,
            "subreddit_id": subreddit_id,
            "score": 0,
            "num_comments": 0,
            "flair": flair,
            "status": status
        }

        self.posts[post_id] = post_info

        return { "success": True, "message": "Post created successfully" }

    def update_post_content(
        self,
        post_id: str,
        title: str = None,
        content: str = None,
        flair: str = None
    ) -> dict:
        """
        Edit the title, content, and/or flair of a Reddit post; only allowed if post status is "active".

        Args:
            post_id (str): The post's unique identifier.
            title (str, optional): New title (leave as None to not change).
            content (str, optional): New post content/body (leave as None to not change).
            flair (str, optional): New flair (leave as None to not change).

        Returns:
            dict:
                - If successful:
                    { "success": True, "message": "Post content updated." }
                - On failure (post not found, post not active, nothing to update):
                    { "success": False, "error": "<reason>" }

        Constraints:
            - Only "active" posts (status == "active") may be edited.
            - At least one field (title, content, or flair) must be provided for update.
        """
        # Check post existence
        if post_id not in self.posts:
            return { "success": False, "error": "Post does not exist." }

        post = self.posts[post_id]

        # Check active status
        if post["status"] != "active":
            return { "success": False, "error": "Only active posts can be updated." }

        # Check if there's anything to update
        update_fields = {}
        if title is not None:
            update_fields["title"] = title
        if content is not None:
            update_fields["content"] = content
        if flair is not None:
            update_fields["flair"] = flair

        if not update_fields:
            return { "success": False, "error": "No fields provided to update." }

        # Apply update
        for k, v in update_fields.items():
            post[k] = v

        # Optionally, update a 'modified' timestamp if present; not in schema

        self.posts[post_id] = post

        return { "success": True, "message": "Post content updated." }

    def delete_post(self, post_id: str) -> dict:
        """
        Marks the post with the given post_id as "deleted" by setting its status, if permitted.

        Args:
            post_id (str): Unique identifier for the post to be deleted.

        Returns:
            dict:
                - On success: { "success": True, "message": "Post <post_id> marked as deleted." }
                - On error: { "success": False, "error": "reason" }

        Constraints:
            - Post must exist.
            - Only posts with a status other than "archived" can be deleted.
            - If already deleted, operation is idempotent and treated as success.
        """
        post = self.posts.get(post_id)
        if not post:
            return { "success": False, "error": f"Post {post_id} does not exist." }

        current_status = post.get("status", "").lower()
        if current_status == "archived":
            return { "success": False, "error": f"Post {post_id} is archived and cannot be deleted." }
        if current_status == "deleted":
            # Already deleted, treat as successful no-op
            return { "success": True, "message": f"Post {post_id} was already deleted." }

        post["status"] = "deleted"
        self.posts[post_id] = post  # Technically not needed, but explicit assignment

        return { "success": True, "message": f"Post {post_id} marked as deleted." }

    def archive_post(self, post_id: str) -> dict:
        """
        Change the status of a post to 'archived', which makes it immutable.

        Args:
            post_id (str): ID of the post to archive.

        Returns:
            dict:
                - On success: {"success": True, "message": "Post <post_id> archived successfully."}
                - On error: {"success": False, "error": "reason"}

        Constraints:
            - The post must exist (valid post_id).
            - If the post is already archived, returns success with an appropriate message.
            - An archived post becomes immutable (other state-modifying operations check for this separately).
        """
        post = self.posts.get(post_id)
        if not post:
            return {"success": False, "error": "Post not found"}

        if post["status"] == "archived":
            return {"success": True, "message": f"Post {post_id} is already archived."}

        post["status"] = "archived"
        self.posts[post_id] = post  # Not strictly needed for dict mutability, but explicit for clarity

        return {"success": True, "message": f"Post {post_id} archived successfully."}

    def restore_post(self, post_id: str) -> dict:
        """
        Revert a "deleted" post back to "active", if allowed by status constraints.

        Args:
            post_id (str): The unique identifier for the post to restore.

        Returns:
            dict: 
                Success: { "success": True, "message": "Post restored to active." }
                Failure (not found): { "success": False, "error": "Post not found." }
                Failure (not deleted): { "success": False, "error": "Post is not deleted." }
                Failure (archived): { "success": False, "error": "Archived post cannot be restored." }

        Constraints:
            - Only posts with status 'deleted' can be restored.
            - Archived posts are immutable and cannot be restored.
        """
        post = self.posts.get(post_id)
        if not post:
            return { "success": False, "error": "Post not found." }
        if post["status"] == "archived":
            return { "success": False, "error": "Archived post cannot be restored." }
        if post["status"] != "deleted":
            return { "success": False, "error": "Post is not deleted." }

        # Restore the post
        post["status"] = "active"
        self.posts[post_id] = post
        return { "success": True, "message": "Post restored to active." }

    def update_post_score(self, post_id: str, new_score: int) -> dict:
        """
        Update the score (ranking/karma) for a Reddit post.

        Args:
            post_id (str): The ID of the post to update.
            new_score (int): The new score to assign to the post.

        Returns:
            dict: {
                "success": True,
                "message": "Score updated for post <post_id>"
            }
            or
            {
                "success": False,
                "error": str  # Description of why update failed
            }

        Constraints:
            - Post must exist.
            - Post status must permit updates (must be 'active').
        """
        post = self.posts.get(post_id)
        if post is None:
            return { "success": False, "error": "Post not found" }
        if post["status"] != "active":
            return { "success": False, "error": "Post status does not allow score update" }
        if not isinstance(new_score, int):
            return { "success": False, "error": "Score must be an integer" }

        post["score"] = new_score
        return { "success": True, "message": f"Score updated for post {post_id}" }

    def update_num_comments(self, post_id: str, num_comments: int) -> dict:
        """
        Update the number of comments for a specific post.

        Args:
            post_id (str): The unique identifier for the post to update.
            num_comments (int): The new value for the number of comments (must be non-negative).

        Returns:
            dict: {
                "success": True,
                "message": "Comment count updated for post <post_id>"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The post must exist in the database.
            - The number of comments must be non-negative.
            - Posts with status "archived" or "deleted" cannot be updated.
        """
        post = self.posts.get(post_id)
        if not post:
            return {"success": False, "error": "Post does not exist"}
        if not isinstance(num_comments, int) or num_comments < 0:
            return {"success": False, "error": "Number of comments must be a non-negative integer"}
        if post["status"] in ("archived", "deleted"):
            return {"success": False, "error": f"Cannot update num_comments: post status is '{post['status']}'"}
        post["num_comments"] = num_comments
        return {"success": True, "message": f"Comment count updated for post {post_id}"}

    def update_author_info(self, author_id: str, username: str = None, account_sta: str = None) -> dict:
        """
        Edit author properties such as username or account status.

        Args:
            author_id (str): The ID of the author whose info is to be updated.
            username (str, optional): The new username to set. If None, not updated.
            account_sta (str, optional): The new account status to set. If None, not updated.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Author info updated for author_id <author_id>" }
                - On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - author_id must exist in self.authors.
            - At least one of username or account_sta must be provided to update.
            - Only valid fields are updated.
        """
        if author_id not in self.authors:
            return { "success": False, "error": f"Author with id '{author_id}' does not exist" }

        if username is None and account_sta is None:
            return { "success": False, "error": "No update fields provided (username/account_sta)" }

        updated = False
        if username is not None:
            self.authors[author_id]['username'] = username
            updated = True
        if account_sta is not None:
            self.authors[author_id]['account_sta'] = account_sta
            updated = True

        if updated:
            return { "success": True, "message": f"Author info updated for author_id {author_id}" }
        else:
            return { "success": False, "error": "No valid fields to update" }

    def update_subreddit_info(
        self, 
        subreddit_id: str, 
        subreddit_name: str = None, 
        description: str = None
    ) -> dict:
        """
        Edit subreddit properties such as its name and/or description.

        Args:
            subreddit_id (str): Unique ID of the subreddit to modify.
            subreddit_name (str, optional): New name for the subreddit.
            description (str, optional): New description for the subreddit.

        Returns:
            dict: 
              - {"success": True, "message": "Subreddit info updated"}
              - {"success": False, "error": <reason>}

        Constraints:
            - Subreddit ID must exist.
            - Only subreddit_name and description may be updated.
        """
        if subreddit_id not in self.subreddits:
            return {"success": False, "error": "Subreddit not found"}

        updated = False
        if subreddit_name is not None:
            self.subreddits[subreddit_id]["subreddit_name"] = subreddit_name
            updated = True
        if description is not None:
            self.subreddits[subreddit_id]["description"] = description
            updated = True

        if not updated:
            return {"success": True, "message": "No changes made to subreddit"}

        return {"success": True, "message": "Subreddit info updated"}


class RedditPostDatabase(BaseEnv):
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

    def get_post_by_id(self, **kwargs):
        return self._call_inner_tool('get_post_by_id', kwargs)

    def get_multiple_posts_by_ids(self, **kwargs):
        return self._call_inner_tool('get_multiple_posts_by_ids', kwargs)

    def list_posts_by_author(self, **kwargs):
        return self._call_inner_tool('list_posts_by_author', kwargs)

    def list_posts_by_subreddit(self, **kwargs):
        return self._call_inner_tool('list_posts_by_subreddit', kwargs)

    def get_author_by_id(self, **kwargs):
        return self._call_inner_tool('get_author_by_id', kwargs)

    def get_subreddit_by_id(self, **kwargs):
        return self._call_inner_tool('get_subreddit_by_id', kwargs)

    def filter_posts_by_status(self, **kwargs):
        return self._call_inner_tool('filter_posts_by_status', kwargs)

    def filter_posts_by_flair(self, **kwargs):
        return self._call_inner_tool('filter_posts_by_flair', kwargs)

    def get_post_metadata(self, **kwargs):
        return self._call_inner_tool('get_post_metadata', kwargs)

    def create_post(self, **kwargs):
        return self._call_inner_tool('create_post', kwargs)

    def update_post_content(self, **kwargs):
        return self._call_inner_tool('update_post_content', kwargs)

    def delete_post(self, **kwargs):
        return self._call_inner_tool('delete_post', kwargs)

    def archive_post(self, **kwargs):
        return self._call_inner_tool('archive_post', kwargs)

    def restore_post(self, **kwargs):
        return self._call_inner_tool('restore_post', kwargs)

    def update_post_score(self, **kwargs):
        return self._call_inner_tool('update_post_score', kwargs)

    def update_num_comments(self, **kwargs):
        return self._call_inner_tool('update_num_comments', kwargs)

    def update_author_info(self, **kwargs):
        return self._call_inner_tool('update_author_info', kwargs)

    def update_subreddit_info(self, **kwargs):
        return self._call_inner_tool('update_subreddit_info', kwargs)

