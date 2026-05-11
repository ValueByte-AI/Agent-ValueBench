# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Any
import uuid
from datetime import datetime
import time
from typing import Optional, Dict, Any



# User entity
class UserInfo(TypedDict):
    _id: str
    username: str
    display_name: str
    preferred_language: str
    account_status: str
    permission: str

# Post entity
class PostInfo(TypedDict):
    post_id: str
    user_id: str  # author
    content: str
    created_at: str  # could be float for timestamp
    language: str
    visibility: str
    status: str
    metadata: Dict[str, Any]

# Comment entity
class CommentInfo(TypedDict):
    comment_id: str
    post_id: str
    user_id: str  # author
    content: str
    created_at: str
    language: str
    status: str
    metadata: Dict[str, Any]

# CommentInteraction entity
class CommentInteractionInfo(TypedDict):
    comment_id: str
    user_id: str
    interaction_type: str  # 'like', 'dislike', 'report'
    timestamp: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}
        # Posts: {post_id: PostInfo}
        self.posts: Dict[str, PostInfo] = {}
        # Comments: {comment_id: CommentInfo}
        self.comments: Dict[str, CommentInfo] = {}
        # Comment Interactions: {comment_id: List[CommentInteractionInfo]}
        self.comment_interactions: Dict[str, List[CommentInteractionInfo]] = {}

        # Constraints:
        # - Only comments with status = 'visible' or 'approved' can be shown to users.
        # - Comments and posts must match the requested language for localization.
        # - Sorting by 'new' uses the created_at timestamp; sorting by 'top' uses interaction metrics.
        # - Users can only access posts/comments based on their permissions and visibility settings.
        # - Metadata for comments and posts can include language, status, and moderation tags.

    def get_post_by_id(self, post_id: str) -> dict:
        """
        Retrieve all details of a post given its post_id.

        Args:
            post_id (str): The unique identifier of the post.

        Returns:
            dict: {
                "success": True,
                "data": PostInfo  # All attributes of the post, if found
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g., post not found
            }

        Constraints:
            - Returns all post details if found, including visibility and language.
            - No user access or visibility checks are performed.
        """
        if post_id not in self.posts:
            return {"success": False, "error": "Post not found"}
        return {"success": True, "data": self.posts[post_id]}

    def list_posts_by_user(self, user_id: str) -> dict:
        """
        List all posts created by a specific user.

        Args:
            user_id (str): The ID of the user whose posts are listed.

        Returns:
            dict:
                - "success": True and "data": list of PostInfo for all posts by this user (empty list if none).
                - "success": False and "error": error message if the user does not exist.

        Constraints:
            - user_id must exist in self.users.
            - Returns all posts by the user, without filtering for status, visibility, or language.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
    
        posts = [
            post for post in self.posts.values()
            if post["user_id"] == user_id
        ]
        return { "success": True, "data": posts }

    def filter_posts_by_language(self, language: str) -> dict:
        """
        Return all posts in the specified language.

        Args:
            language (str): The language code to filter posts by.

        Returns:
            dict: {
                "success": True,
                "data": List[PostInfo],  # List of posts in the requested language
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., invalid language)
            }

        Constraints:
            - Only posts with PostInfo['language'] == language are returned.
            - Returns an empty list if no posts match.
            - If language is empty or None, returns error.
        """
        if not language or not isinstance(language, str):
            return {"success": False, "error": "Invalid or missing language parameter."}

        result = [
            post_info for post_info in self.posts.values()
            if post_info.get("language") == language
        ]

        return {"success": True, "data": result}

    def filter_posts_by_visibility(self, visibility: str) -> dict:
        """
        Return all posts matching the specified visibility level.

        Args:
            visibility (str): The visibility level to filter posts by ('public', 'private', etc.)

        Returns:
            dict:
                success (bool): True if query is successful.
                data (List[PostInfo]): List of PostInfo objects with the specified visibility.
    
        Notes:
            - If no posts match the given visibility, returns an empty data list.
            - No error is returned for an unknown visibility value; the result is just empty.
        """
        result = [
            post for post in self.posts.values()
            if post["visibility"] == visibility
        ]
        return { "success": True, "data": result }

    def get_comments_by_post_id(self, post_id: str) -> dict:
        """
        Retrieve all comments (with full metadata) associated with a given post_id.

        Args:
            post_id (str): The ID of the post whose comments are to be retrieved.

        Returns:
            dict: 
                - If post_id exists:
                    { "success": True, "data": List[CommentInfo] }
                - If post_id does not exist:
                    { "success": False, "error": "Post does not exist" }

        Constraints:
            - The post_id must exist in the system.
            - No filtering on comment status or language is performed — all comments with matching post_id are returned.
        """
        if post_id not in self.posts:
            return { "success": False, "error": "Post does not exist" }

        comments = [
            comment_info for comment_info in self.comments.values()
            if comment_info["post_id"] == post_id
        ]

        return { "success": True, "data": comments }

    def filter_comments_by_language(self, comment_ids: list, language: str) -> dict:
        """
        Filter given comments by the specified language.

        Args:
            comment_ids (list of str): List of comment IDs to filter.
            language (str): The language code to filter by.

        Returns:
            dict:
                - success (bool): True if processed.
                - data (list of CommentInfo): Comments (from input list) whose 'language' matches.
                - error (str, optional): Error description if input is invalid.

        Constraints:
            - Missing comment IDs in self.comments are ignored.
            - No permissions or status constraints enforced.

        Edge cases:
            - If input list is empty or no matches, success with empty data list.

        """
        if not isinstance(comment_ids, list) or not isinstance(language, str):
            return {
                "success": False,
                "error": "Invalid input types for comment_ids or language"
            }

        filtered = [
            self.comments[cid]
            for cid in comment_ids
            if cid in self.comments and self.comments[cid].get("language") == language
        ]
        return {"success": True, "data": filtered}

    def filter_comments_by_status(self) -> dict:
        """
        Filter and return all comments with status 'visible' or 'approved'.

        Returns:
            dict: {
                "success": True,
                "data": List[CommentInfo],  # List of comments (possibly empty)
            }

        Constraints:
            - Only comments where status == 'visible' or status == 'approved' are included.
        """
        filtered_comments = [
            comment_info for comment_info in self.comments.values()
            if comment_info['status'] in ('visible', 'approved')
        ]
        return {
            "success": True,
            "data": filtered_comments
        }

    def sort_comments_by_new(self, post_id: str) -> dict:
        """
        Sort and retrieve all comments for a given post_id, including only comments with status 'visible' or 'approved',
        ordered by created_at (newest first).

        Args:
            post_id (str): The ID of the post whose comments are to be sorted.

        Returns:
            dict: {
                "success": True,
                "data": List[CommentInfo],  # Sorted (newest first), may be empty if no qualifying comments
            }
            or
            {
                "success": False,
                "error": str  # Description of failure (e.g., post_id not found)
            }

        Constraints:
            - Only comments with status 'visible' or 'approved' are considered.
            - All comments sorted by created_at (descending).
            - If post_id does not exist, return error.
        """
        if post_id not in self.posts:
            return { "success": False, "error": "Post ID does not exist" }

        # Filter relevant comments
        relevant_comments = [
            comment for comment in self.comments.values()
            if comment['post_id'] == post_id and comment['status'] in ['visible', 'approved']
        ]

        # Sort by created_at descending (newest first)
        sorted_comments = sorted(
            relevant_comments,
            key=lambda c: c['created_at'],
            reverse=True    # newest first
        )

        return { "success": True, "data": sorted_comments }

    def count_comment_interactions(self, comment_id: str) -> dict:
        """
        Returns the count of each interaction type (like, dislike, report) for a given comment.

        Args:
            comment_id (str): The identifier of the comment.

        Returns:
            dict:
             - On success:
                 {
                     "success": True,
                     "data": {"like": int, "dislike": int, "report": int}
                 }
             - On failure:
                 {
                     "success": False,
                     "error": "Comment not found"
                 }

        Constraints:
            - The comment must exist.
            - "like", "dislike", and "report" must appear in the result even if their counts are zero.
        """
        if comment_id not in self.comments:
            return { "success": False, "error": "Comment not found" }
    
        interaction_types = ["like", "dislike", "report"]
        counts = {k: 0 for k in interaction_types}
    
        for interaction in self.comment_interactions.get(comment_id, []):
            typ = interaction.get("interaction_type")
            if typ in counts:
                counts[typ] += 1

        return { "success": True, "data": counts }

    def sort_comments_by_top(self, post_id: str) -> dict:
        """
        Sort the comments of a post by their interaction metric ("top"/most liked).

        Only comments with status 'visible' or 'approved' are included.
        The result is sorted descending by the number of 'like' interactions.

        Args:
            post_id (str): The ID of the post whose comments are to be sorted.

        Returns:
            dict: 
                - success: True
                  data: List[CommentInfo], sorted from most to least likes
                - success: False, error: str (problem description)
    
        Constraints:
            - Only comments with status 'visible' or 'approved' are shown.
            - Sorting metric is the count of 'like' interactions per comment.
            - If post_id does not exist, return an error.
        """
        if post_id not in self.posts:
            return { "success": False, "error": "Post not found" }
    
        VISIBLE_STATUSES = {"visible", "approved"}
        # Filter relevant comments
        filtered_comments = [
            comment for comment in self.comments.values()
            if comment["post_id"] == post_id and comment["status"] in VISIBLE_STATUSES
        ]

        # For each comment, count number of 'like' interactions
        def like_count(comment_id: str) -> int:
            interactions = self.comment_interactions.get(comment_id, [])
            return sum(1 for interaction in interactions if interaction["interaction_type"] == "like")

        comments_with_likes = [
            (comment, like_count(comment["comment_id"])) for comment in filtered_comments
        ]

        # Sort descending by likes, then by created_at (newer ones first if tie)
        sorted_comments = sorted(
            comments_with_likes,
            key=lambda item: (-item[1], item[0]["created_at"]),
        )

        sorted_comment_infos = [item[0] for item in sorted_comments]

        return {
            "success": True,
            "data": sorted_comment_infos
        }

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve all attributes of a user by user_id.

        Args:
            user_id (str): The unique ID of the user to look up.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo  # User attributes dictionary
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., "User does not exist"
            }
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}
        return {"success": True, "data": self.users[user_id]}

    def check_user_permission_for_post(self, user_id: str, post_id: str) -> dict:
        """
        Checks whether a user can access a post, based on permission and post visibility.

        Args:
            user_id (str): The user's unique identifier.
            post_id (str): The post's unique identifier.

        Returns:
            dict: {
                "success": True,
                "has_permission": bool  # Whether the user may access the post.
            }
            or
            {
                "success": False,
                "error": str  # Description, if user or post not found.
            }

        Constraints/Rules:
            - Only users with required permission and account status can access posts with applicable visibility.
            - Possible post visibility settings: 'public', 'private', and custom. Only 'public' supported by default for all users.
            - Post author and admins can always access their posts.
            - If user's account_status != 'active', deny access.
        """
        # Validate user
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User does not exist"}
        # Validate post
        post = self.posts.get(post_id)
        if not post:
            return {"success": False, "error": "Post does not exist"}

        # If banned/suspended etc, deny access
        if user.get('account_status') != 'active':
            return {"success": True, "has_permission": False}

        user_permission = user.get('permission', '')
        post_visibility = post.get('visibility', '')
        post_author_id = post.get('user_id', '')
        post_status = post.get('status', '')

        # Admins can always access
        if user_permission in ['admin', 'moderator']:
            return {"success": True, "has_permission": True}

        # Author can always see their own post
        if user_id == post_author_id:
            return {"success": True, "has_permission": True}

        # Only allow non-author, non-admin access to showable posts.
        if post_status not in ['visible', 'approved', 'active']:
            return {"success": True, "has_permission": False}

        # Visibility logic
        if post_visibility == 'public':
            return {"success": True, "has_permission": True}
        elif post_visibility == 'private':
            # Only the author or admins, handled already
            return {"success": True, "has_permission": False}
        elif post_visibility == 'friends':
            # No friends relation in present state; cannot approve access.
            return {"success": True, "has_permission": False}
        else:
            # Unknown visibility, do not allow access
            return {"success": True, "has_permission": False}

    def check_user_permission_for_comment(self, user_id: str, comment_id: str) -> dict:
        """
        Verify whether a user can access a comment, based on the user's permission, 
        the comment's status, and the parent post's visibility.

        Args:
            user_id (str): ID of the user requesting access.
            comment_id (str): ID of the comment to check access for.

        Returns:
            dict: 
                - On entity lookup failure:
                    { "success": False, "error": "<reason>" }
                - On permission check (successfully checked):
                    { "success": True, "permitted": True }
                    or
                    { "success": True, "permitted": False, "reason": "<reason>" }
        Constraints:
            - Only comments with status 'visible' or 'approved' can be viewed.
            - Posts/comments must be accessible according to user permission and post visibility.
            - User must exist and not have banned/inactive account status.
        """

        # 1. Lookup user
        user = self.users.get(user_id)
        if user is None:
            return {"success": False, "error": "User does not exist"}

        if user.get("account_status", "active") not in ("active",):  # treat only 'active' as valid
            return {"success": True, "permitted": False, "reason": "User account is not active"}

        # 2. Lookup comment
        comment = self.comments.get(comment_id)
        if comment is None:
            return {"success": False, "error": "Comment does not exist"}

        # 3. Check comment status
        if comment.get("status") not in ("visible", "approved"):
            return {"success": True, "permitted": False, "reason": "Comment is not visible"}

        # 4. Lookup post
        post_id = comment.get("post_id")
        post = self.posts.get(post_id)
        if post is None:
            return {"success": False, "error": "Parent post does not exist"}

        # 5. Check post visibility and user permissions
        post_visibility = post.get("visibility", "public")
        user_permission = user.get("permission", "user")

        # Access rules (example inference, can be extended based on roles):
        # - If post is 'public', all non-banned users can access.
        # - If post is 'private', only the author, moderators, or admins can access.
        # - If post is 'friends', only author or friends (in this domain, we assume NO friends implemented; so author or staff).
        # (Lack of specifics; basic blocking)

        permitted = False
        reason = ""

        if post_visibility == "public":
            permitted = True
        elif post_visibility == "private":
            if user_permission in ("admin", "moderator"):
                permitted = True
            elif post.get("user_id") == user_id:
                permitted = True
            else:
                reason = "Post is private"
        elif post_visibility == "friends":
            if user_permission in ("admin", "moderator"):
                permitted = True
            elif post.get("user_id") == user_id:
                permitted = True
            else:
                reason = "Post is visible only to friends or staff"
        else:
            reason = f"Post visibility '{post_visibility}' unknown or not permitted"
    
        if permitted:
            return { "success": True, "permitted": True }
        else:
            return { "success": True, "permitted": False, "reason": reason or "Not permitted by visibility/permissions" }

    def get_comment_by_id(self, comment_id: str) -> dict:
        """
        Retrieve all information about a comment by its comment_id.

        Args:
            comment_id (str): The unique identifier of the comment.

        Returns:
            dict: On success:
                      {
                          "success": True,
                          "data": CommentInfo  # The comment metadata dict
                      }
                  On failure (comment does not exist):
                      {
                          "success": False,
                          "error": "Comment not found"
                      }

        Constraints:
            - No permission or status checking required; simply returns record if it exists.
        """
        if comment_id not in self.comments:
            return { "success": False, "error": "Comment not found" }
        return { "success": True, "data": self.comments[comment_id] }

    def get_comments_for_post_sorted_and_filtered(
        self,
        post_id: str,
        status: list = None,
        language: str = None,
        sort_by: str = "new"
    ) -> dict:
        """
        Retrieve comments for a given post_id, filtered by status and language, and sorted by either 'new' or 'top'.

        Args:
            post_id (str): ID of the post whose comments to retrieve.
            status (list, optional): List of allowed statuses ('visible', 'approved', etc.). Defaults to ['visible', 'approved'].
            language (str, optional): Filter only comments with this language code.
            sort_by (str): Either 'new' (most recent first), or 'top' (most likes/upvotes first).

        Returns:
            dict: {
                "success": True,
                "data": List[CommentInfo]  # sorted, filtered list of comments
            }
            OR
            {
                "success": False,
                "error": str  # error reason
            }

        Constraints/Rules:
            - Comments must have a status accepted in the platform ('visible'/'approved') (either by default or as filtered).
            - Language filtering matches comment["language"].
            - 'new': sort by 'created_at' (descending).
            - 'top': sort by number of 'like' interactions (descending).
        """
        # Validate post_id exists
        if post_id not in self.posts:
            return {"success": False, "error": "Post does not exist"}

        # Default status filter to ['visible', 'approved'] if not provided
        if status is None:
            status_set = {'visible', 'approved'}
        else:
            status_set = set(status)

        # Gather relevant comments
        filtered_comments = []
        for comment in self.comments.values():
            if comment["post_id"] != post_id:
                continue
            if comment["status"] not in status_set:
                continue
            if language is not None and comment["language"] != language:
                continue
            filtered_comments.append(comment)

        # Sorting
        if sort_by == "new":
            # Sort by created_at descending (most recent first)
            # Assume created_at can be compared as string or timestamp
            filtered_comments.sort(key=lambda c: c["created_at"], reverse=True)
        elif sort_by == "top":
            # Sort by number of 'like' interactions descending
            def like_count(comment):
                interactions = self.comment_interactions.get(comment["comment_id"], [])
                return sum(1 for i in interactions if i.get("interaction_type") == "like")
            filtered_comments.sort(key=like_count, reverse=True)
        else:
            return {"success": False, "error": "Unknown sort_by option"}

        return {"success": True, "data": filtered_comments}

    def get_comment_interactions(self, comment_id: str) -> dict:
        """
        Retrieve the full list of interactions (like, dislike, report, etc.) associated with a specific comment.

        Args:
            comment_id (str): The unique identifier for the comment.

        Returns:
            dict: {
                "success": True,
                "data": List[CommentInteractionInfo],  # May be empty if no interactions exist
            }
            or
            {
                "success": False,
                "error": str  # Description of error, e.g. comment does not exist
            }

        Constraints:
            - The comment must exist in the system.
        """
        if comment_id not in self.comments:
            return { "success": False, "error": "Comment does not exist" }

        interactions = self.comment_interactions.get(comment_id, [])
        return { "success": True, "data": interactions }


    def create_post(
        self,
        user_id: str,
        content: str,
        language: str,
        visibility: str,
        metadata: dict = None
    ) -> dict:
        """
        Add a new post for a user with given content, language, and visibility settings.

        Args:
            user_id (str): The ID of the user creating the post.
            content (str): The content of the post.
            language (str): The language code for the post.
            visibility (str): The visibility setting of the post.
            metadata (dict, optional): Additional metadata for the post.

        Returns:
            dict: {
                "success": True,
                "message": "Post created with post_id <post_id>."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
          - user_id must refer to an existing, active (not banned/inactive) user
          - Each post_id is unique (system-generated)
        """
        # Check user exists
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User not found."}
        if user['account_status'].lower() not in ('active', 'enabled'):
            return {"success": False, "error": "User account not active."}
        if not content or not language or not visibility:
            return {"success": False, "error": "Missing required post fields."}

        # Generate unique post ID
        post_id = str(uuid.uuid4())
        # Creation timestamp (ISO format)
        created_at = datetime.utcnow().isoformat()

        post_info = {
            "post_id": post_id,
            "user_id": user_id,
            "content": content,
            "created_at": created_at,
            "language": language,
            "visibility": visibility,
            "status": "visible",
            "metadata": metadata if metadata is not None else {}
        }
        self.posts[post_id] = post_info

        return {"success": True, "message": f"Post created with post_id {post_id}."}

    def update_post_visibility(self, post_id: str, new_visibility: str) -> dict:
        """
        Change the visibility level of a post.

        Args:
            post_id (str): The unique identifier of the post to update.
            new_visibility (str): The new visibility level (e.g., 'public', 'private', 'friends').

        Returns:
            dict: {
                "success": True,
                "message": "Post visibility updated."
            }
            or
            {
                "success": False,
                "error": "Post not found"
            }

        Constraints:
            - The post must exist.
            - Visibility is updated directly; no permission or value checking required by spec.
        """
        post = self.posts.get(post_id)
        if not post:
            return { "success": False, "error": "Post not found" }

        post['visibility'] = new_visibility
        # Optionally update a 'modified_at' time in metadata (not required by spec).

        return { "success": True, "message": "Post visibility updated." }

    def update_post_status(self, post_id: str, new_status: str) -> dict:
        """
        Change the moderation status of a post.

        Args:
            post_id (str): The ID of the post whose status should be updated.
            new_status (str): The new moderation status string (e.g., 'approved', 'removed', etc.).

        Returns:
            dict: {
                "success": True,
                "message": "Post status updated."
            }
            or
            {
                "success": False,
                "error": "Post not found."
            }

        Constraints:
            - post_id must exist in the platform backend's posts.
            - No explicit whitelist for status values (any string accepted).
        """
        if post_id not in self.posts:
            return { "success": False, "error": "Post not found." }
    
        self.posts[post_id]['status'] = new_status
        return { "success": True, "message": "Post status updated." }

    def delete_post(self, post_id: str) -> dict:
        """
        Remove a post (and its associated comments and comment interactions) from the backend.
    
        Args:
            post_id (str): The unique identifier of the post to remove.

        Returns:
            dict: {
                "success": True,
                "message": str  # Success message on deletion,
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - The post must exist.
            - All associated comments and comment interactions for this post are also removed for consistency.
        """
        if post_id not in self.posts:
            return {"success": False, "error": "Post does not exist"}

        # Remove the post
        del self.posts[post_id]

        # Remove associated comments and their interactions
        to_remove_comments = [cid for cid, cinfo in self.comments.items() if cinfo["post_id"] == post_id]
        for cid in to_remove_comments:
            del self.comments[cid]
            if cid in self.comment_interactions:
                del self.comment_interactions[cid]

        return {
            "success": True, 
            "message": f"Post '{post_id}' and associated comments have been deleted"
        }


    def create_comment(
        self, 
        post_id: str, 
        user_id: str, 
        content: str, 
        language: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> dict:
        """
        Add a new comment to a post.

        Args:
            post_id (str): ID of the post to comment on. Must exist.
            user_id (str): ID of the commenting user. Must exist and be allowed to comment.
            content (str): Text content of the comment. Must not be empty.
            language (str): Language of the comment (for localization).
            metadata (dict, optional): Additional metadata for the comment.

        Returns:
            dict: {
                "success": True,
                "message": "Comment created",
                "comment_id": str
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The post must exist.
            - The user must exist and not be banned.
            - Comment content must not be empty.
            - Each comment must have a unique comment_id.
            - Set created_at to current time.
            - Status is usually set to 'visible' by default.
        """
        # Check post exists
        if post_id not in self.posts:
            return {"success": False, "error": "Post does not exist"}
    
        # Check user exists and is active
        user = self.users.get(user_id)
        if user is None:
            return {"success": False, "error": "User does not exist"}
        if user.get("account_status") != "active":
            return {"success": False, "error": "User account is not active"}
    
        # Content non-empty
        if not isinstance(content, str) or len(content.strip()) == 0:
            return {"success": False, "error": "Comment content is empty"}
    
        # Normally would check visibility/status/permission if more info about roles

        # Set status as 'visible' by default
        status = "visible"

        # Generate new unique comment_id
        new_comment_id = str(uuid.uuid4())
        while new_comment_id in self.comments:  # Extremely unlikely, but safe
            new_comment_id = str(uuid.uuid4())
    
        now_str = str(time.time())
        new_comment = {
            "comment_id": new_comment_id,
            "post_id": post_id,
            "user_id": user_id,
            "content": content.strip(),
            "created_at": now_str,
            "language": language,
            "status": status,
            "metadata": metadata if metadata is not None else {},
        }
        self.comments[new_comment_id] = new_comment

        # Comment interactions start empty (can be created on interaction)
        self.comment_interactions[new_comment_id] = []

        return {
            "success": True,
            "message": "Comment created",
            "comment_id": new_comment_id
        }

    def update_comment_status(self, comment_id: str, new_status: str) -> dict:
        """
        Change the moderation status of a specific comment.

        Args:
            comment_id (str): The unique identifier of the comment to update.
            new_status (str): The new moderation status to set (e.g., 'approved', 'visible', 'hidden').

        Returns:
            dict:
                On success: { "success": True, "message": "Comment status updated." }
                On failure: { "success": False, "error": <reason str> }

        Constraints:
            - The comment must exist.
            - (If applicable) The new_status should be a valid status string.
        """
        if comment_id not in self.comments:
            return { "success": False, "error": "Comment does not exist." }

        # (Optional: enforce allowed status values. If not specified, skip.)
        # allowed_statuses = {"visible", "approved", "hidden", "flagged", "pending"}
        # if new_status not in allowed_statuses:
        #     return { "success": False, "error": "Invalid status value." }

        self.comments[comment_id]['status'] = new_status
        return { "success": True, "message": "Comment status updated." }

    def update_comment_language(self, comment_id: str, new_language: str) -> dict:
        """
        Change the language metadata of a comment.

        Args:
            comment_id (str): The ID of the comment to update.
            new_language (str): The new language code to assign.

        Returns:
            dict: 
                { "success": True, "message": "Comment language updated" }
                or
                { "success": False, "error": "Comment not found" }

        Constraints:
            - Only updates if the comment exists.
            - No permission or status checks for this backend operation.
            - Updates both the `language` attribute and the 'language' in `metadata` if present.
        """
        comment = self.comments.get(comment_id)
        if not comment:
            return { "success": False, "error": "Comment not found" }
    
        comment["language"] = new_language
        if comment.get("metadata") is not None:
            comment["metadata"]["language"] = new_language
    
        return { "success": True, "message": "Comment language updated" }

    def delete_comment(self, comment_id: str, requesting_user_id: str) -> dict:
        """
        Remove a comment, enforcing permission rules.

        Args:
            comment_id (str): ID of the comment to delete.
            requesting_user_id (str): ID of the user requesting deletion.

        Returns:
            dict: 
                On success: { "success": True, "message": "Comment deleted." }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - Only the author of the comment, or a user with 'moderator'/'admin' permission, can delete the comment.
            - On delete, also remove all associated comment interactions.
        """
        # Check if comment exists
        comment = self.comments.get(comment_id)
        if not comment:
            return {"success": False, "error": "Comment does not exist."}

        # Check if requesting user exists
        user = self.users.get(requesting_user_id)
        if not user:
            return {"success": False, "error": "Requesting user does not exist."}

        # Permission logic:
        # Author can delete, or 'moderator'/'admin' can delete any
        user_permission = user.get("permission", "")
        is_author = (requesting_user_id == comment["user_id"])
        if not (is_author or user_permission in ("moderator", "admin")):
            return {"success": False, "error": "Permission denied: cannot delete this comment."}

        # Remove comment
        del self.comments[comment_id]

        # Remove all comment interactions if present
        if comment_id in self.comment_interactions:
            del self.comment_interactions[comment_id]

        return {"success": True, "message": "Comment deleted."}

    def add_comment_interaction(
        self,
        comment_id: str,
        user_id: str,
        interaction_type: str,
        timestamp: str
    ) -> dict:
        """
        Register an interaction (like, dislike, report) by a user on a comment.

        Args:
            comment_id (str): The ID of the comment to interact with.
            user_id (str): ID of the user performing the action.
            interaction_type (str): 'like', 'dislike', or 'report'.
            timestamp (str): When the interaction is registered.

        Returns:
            dict: 
                - { "success": True, "message": "Interaction registered" }
                - { "success": False, "error": <reason> }

        Constraints:
            - Comment and user must exist.
            - interaction_type must be one of 'like', 'dislike', 'report'.
            - One 'like' or 'dislike' per user per comment; write/update.
            - Multiple 'report' interactions allowed by same user on same comment.
        """
        valid_types = {'like', 'dislike', 'report'}

        # Check comment exists
        if comment_id not in self.comments:
            return { "success": False, "error": "Comment does not exist" }
    
        # Check user exists
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        # Check interaction type
        if interaction_type not in valid_types:
            return { "success": False, "error": "Invalid interaction type" }

        # Ensure per-comment interaction list exists
        if comment_id not in self.comment_interactions:
            self.comment_interactions[comment_id] = []

        interactions = self.comment_interactions[comment_id]
        if interaction_type in ('like', 'dislike'):
            # Remove existing like/dislike of same type from this user on this comment
            found = False
            for i, inter in enumerate(interactions):
                if inter["user_id"] == user_id and inter["interaction_type"] in ('like', 'dislike'):
                    if inter["interaction_type"] == interaction_type:
                        # Update timestamp if same type
                        interactions[i]["timestamp"] = timestamp
                        found = True
                        break
                    else:
                        # Remove the other type (like<->dislike switch)
                        interactions.pop(i)
                        break
            if not found:
                # Add the new interaction
                new_interaction = {
                    "comment_id": comment_id,
                    "user_id": user_id,
                    "interaction_type": interaction_type,
                    "timestamp": timestamp
                }
                interactions.append(new_interaction)
        elif interaction_type == "report":
            # Allow multiple reports from the same user
            new_interaction = {
                "comment_id": comment_id,
                "user_id": user_id,
                "interaction_type": interaction_type,
                "timestamp": timestamp
            }
            interactions.append(new_interaction)
    
        self.comment_interactions[comment_id] = interactions
        return { "success": True, "message": "Interaction registered" }

    def remove_comment_interaction(self, comment_id: str, user_id: str, interaction_type: str) -> dict:
        """
        Remove a specific recorded interaction (like, dislike, report) from a comment by a user.

        Args:
            comment_id (str): ID of the comment whose interaction should be removed.
            user_id (str): ID of the user whose interaction should be removed.
            interaction_type (str): Type of interaction ('like', 'dislike', 'report').

        Returns:
            dict:
                On success: { "success": True, "message": "Interaction removed from comment." }
                On failure: { "success": False, "error": str }
    
        Constraints:
            - The comment is assumed to exist.
            - The interaction must exist (performed by the user, on that comment, and of that type).
        """
        # Optional: check if comment exists
        if comment_id not in self.comments:
            return { "success": False, "error": "Comment does not exist." }

        interactions = self.comment_interactions.get(comment_id, [])
        found = False
        for i, interaction in enumerate(interactions):
            if (
                interaction['user_id'] == user_id and
                interaction['interaction_type'] == interaction_type
            ):
                found = True
                del interactions[i]
                # Update mapping in case of direct pointer (modify in place)
                self.comment_interactions[comment_id] = interactions
                break

        if not found:
            return { "success": False, "error": "Interaction not found for this user and type." }

        return { "success": True, "message": "Interaction removed from comment." }

    def update_comment_metadata(self, comment_id: str, metadata_updates: dict) -> dict:
        """
        Update or add metadata tags for a comment.

        Args:
            comment_id (str): The unique ID of the comment to update.
            metadata_updates (dict): Key-value pairs to set/update in the comment's metadata.

        Returns:
            dict:
                On success: { "success": True, "message": "Comment metadata updated." }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - comment_id must correspond to an existing comment.
            - metadata_updates must be a dictionary.
            - Updates will overwrite existing keys or add new ones in the metadata.
        """
        if comment_id not in self.comments:
            return { "success": False, "error": "Comment does not exist." }

        if not isinstance(metadata_updates, dict):
            return { "success": False, "error": "metadata_updates must be a dictionary." }

        # Get current metadata, ensure it's a dict
        current_metadata = self.comments[comment_id].get("metadata")
        if not isinstance(current_metadata, dict):
            current_metadata = {}
            self.comments[comment_id]["metadata"] = current_metadata

        # Update metadata
        current_metadata.update(metadata_updates)

        return { "success": True, "message": "Comment metadata updated." }

    def update_post_metadata(self, post_id: str, metadata_updates: dict) -> dict:
        """
        Add or update metadata tags for a specific post.

        Args:
            post_id (str): ID of the post whose metadata should be modified.
            metadata_updates (dict): Dictionary of key-value pairs to add/update in the post's metadata.

        Returns:
            dict: {
                "success": True,
                "message": "Post metadata updated."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - The post must exist.
            - Only updates existing/sets new metadata fields.
            - No restrictions on the keys/values in metadata_updates.
        """
        if post_id not in self.posts:
            return { "success": False, "error": "Post not found." }
        if not isinstance(metadata_updates, dict):
            return { "success": False, "error": "metadata_updates must be a dictionary." }

        # Update metadata
        post_info = self.posts[post_id]
        if "metadata" not in post_info or not isinstance(post_info["metadata"], dict):
            post_info["metadata"] = {}

        post_info["metadata"].update(metadata_updates)

        return { "success": True, "message": "Post metadata updated." }

    def ban_user(self, user_id: str, ban_type: str) -> dict:
        """
        Change the account_status of a user to 'banned' or 'suspended'.

        Args:
            user_id (str): ID of the user to ban.
            ban_type (str): Type of ban ('banned' or 'suspended').

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
            - Only valid if user exists.
            - ban_type must be 'banned' or 'suspended'.
            - Updates the user's account_status field.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }
        if ban_type not in ("banned", "suspended"):
            return { "success": False, "error": "Invalid ban type" }
    
        current_status = self.users[user_id]['account_status']
        if current_status == ban_type:
            return {
                "success": True,
                "message": f"User {user_id} account_status is already {ban_type}"
            }
        self.users[user_id]['account_status'] = ban_type
        return {
            "success": True,
            "message": f"User {user_id} account_status set to {ban_type}"
        }

    def change_user_permissions(self, user_id: str, new_permission: str) -> dict:
        """
        Update the permission level of a specified user.

        Args:
            user_id (str): The unique identifier of the user whose permission is to be updated.
            new_permission (str): The new permission level to assign.

        Returns:
            dict:
                - On success:
                    { "success": True, "message": "Permission updated for user <user_id>" }
                - On failure:
                    { "success": False, "error": "<reason>" }

        Constraints:
            - The user with the given user_id must exist.
            - The new_permission should be a non-empty string. Optionally, should match allowed permission values if known.
        """
        if user_id not in self.users:
            return { "success": False, "error": f"User '{user_id}' does not exist" }
        if not isinstance(new_permission, str) or not new_permission.strip():
            return { "success": False, "error": "Invalid new_permission: must be a non-empty string" }

        self.users[user_id]["permission"] = new_permission.strip()
        return { "success": True, "message": f"Permission updated for user {user_id}" }


class SocialMediaPlatformBackend(BaseEnv):
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

    def list_posts_by_user(self, **kwargs):
        return self._call_inner_tool('list_posts_by_user', kwargs)

    def filter_posts_by_language(self, **kwargs):
        return self._call_inner_tool('filter_posts_by_language', kwargs)

    def filter_posts_by_visibility(self, **kwargs):
        return self._call_inner_tool('filter_posts_by_visibility', kwargs)

    def get_comments_by_post_id(self, **kwargs):
        return self._call_inner_tool('get_comments_by_post_id', kwargs)

    def filter_comments_by_language(self, **kwargs):
        return self._call_inner_tool('filter_comments_by_language', kwargs)

    def filter_comments_by_status(self, **kwargs):
        return self._call_inner_tool('filter_comments_by_status', kwargs)

    def sort_comments_by_new(self, **kwargs):
        return self._call_inner_tool('sort_comments_by_new', kwargs)

    def count_comment_interactions(self, **kwargs):
        return self._call_inner_tool('count_comment_interactions', kwargs)

    def sort_comments_by_top(self, **kwargs):
        return self._call_inner_tool('sort_comments_by_top', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def check_user_permission_for_post(self, **kwargs):
        return self._call_inner_tool('check_user_permission_for_post', kwargs)

    def check_user_permission_for_comment(self, **kwargs):
        return self._call_inner_tool('check_user_permission_for_comment', kwargs)

    def get_comment_by_id(self, **kwargs):
        return self._call_inner_tool('get_comment_by_id', kwargs)

    def get_comments_for_post_sorted_and_filtered(self, **kwargs):
        return self._call_inner_tool('get_comments_for_post_sorted_and_filtered', kwargs)

    def get_comment_interactions(self, **kwargs):
        return self._call_inner_tool('get_comment_interactions', kwargs)

    def create_post(self, **kwargs):
        return self._call_inner_tool('create_post', kwargs)

    def update_post_visibility(self, **kwargs):
        return self._call_inner_tool('update_post_visibility', kwargs)

    def update_post_status(self, **kwargs):
        return self._call_inner_tool('update_post_status', kwargs)

    def delete_post(self, **kwargs):
        return self._call_inner_tool('delete_post', kwargs)

    def create_comment(self, **kwargs):
        return self._call_inner_tool('create_comment', kwargs)

    def update_comment_status(self, **kwargs):
        return self._call_inner_tool('update_comment_status', kwargs)

    def update_comment_language(self, **kwargs):
        return self._call_inner_tool('update_comment_language', kwargs)

    def delete_comment(self, **kwargs):
        return self._call_inner_tool('delete_comment', kwargs)

    def add_comment_interaction(self, **kwargs):
        return self._call_inner_tool('add_comment_interaction', kwargs)

    def remove_comment_interaction(self, **kwargs):
        return self._call_inner_tool('remove_comment_interaction', kwargs)

    def update_comment_metadata(self, **kwargs):
        return self._call_inner_tool('update_comment_metadata', kwargs)

    def update_post_metadata(self, **kwargs):
        return self._call_inner_tool('update_post_metadata', kwargs)

    def ban_user(self, **kwargs):
        return self._call_inner_tool('ban_user', kwargs)

    def change_user_permissions(self, **kwargs):
        return self._call_inner_tool('change_user_permissions', kwargs)
