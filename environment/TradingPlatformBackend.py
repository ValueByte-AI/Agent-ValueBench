# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, Optional, TypedDict
from datetime import datetime
import uuid
import time



# Maps to: IdeaPos entity
class IdeaPostInfo(TypedDict):
    idea_id: str  # UUID
    author_id: str
    content: str
    timestamp: str
    visibility: str
    tags: List[str]
    vote_count: int

# Maps to: Comme (Comment) entity
class CommentInfo(TypedDict):
    comment_id: str  # UUID
    idea_id: str
    author_id: str
    content: str
    timestamp: str
    parent_comment_id: Optional[str]
    vote_count: int

# Maps to: User entity
class UserInfo(TypedDict):
    _id: str
    username: str
    reputation: int
    profile_info: str
    joined_date: str

# Maps to: Vote entity
class VoteInfo(TypedDict):
    vote_id: str
    voter_id: str
    target_type: str  # 'idea' or 'comment'
    target_id: str
    vote_value: int
    timestamp: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Key: idea_id (UUID), Value: IdeaPostInfo
        self.ideas: Dict[str, IdeaPostInfo] = {}
        # Key: comment_id (UUID), Value: CommentInfo
        self.comments: Dict[str, CommentInfo] = {}
        # Key: user_id, Value: UserInfo
        self.users: Dict[str, UserInfo] = {}
        # Key: vote_id, Value: VoteInfo
        self.votes: Dict[str, VoteInfo] = {}

        # Constraints (to be enforced in relevant operations):
        # - Every idea post must have a unique idea_id (UUID).
        # - Comments must be linked to a valid idea_id.
        # - Comments can be threaded (parent_comment_id may be null or another comment_id for replies).
        # - Deleting a user or idea should handle associated comments and votes appropriately (cascade or anonymize).
        # - Users cannot vote more than once on the same target.

    def get_idea_by_id(self, idea_id: str) -> dict:
        """
        Fetch the details of a specific idea post using its unique idea_id.

        Args:
            idea_id (str): The UUID identifying the idea post.

        Returns:
            dict: If successful, returns
                  { "success": True, "data": IdeaPostInfo }
                  If not found, returns
                  { "success": False, "error": "Idea post not found" }

        Constraints:
            - The idea_id must correspond to an existing idea post.
        """
        idea = self.ideas.get(idea_id)
        if idea is None:
            return { "success": False, "error": "Idea post not found" }
        return { "success": True, "data": idea }

    def list_ideas_by_user(self, user_id: str) -> dict:
        """
        Retrieve all idea posts authored by a particular user.

        Args:
            user_id (str): The unique identifier of the user whose ideas are requested.

        Returns:
            dict: {
                "success": True,
                "data": List[IdeaPostInfo],  # List of the user's ideas (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # E.g., User does not exist
            }

        Constraints:
            - User must exist in the system.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        ideas = [
            idea for idea in self.ideas.values()
            if idea["author_id"] == user_id
        ]

        return { "success": True, "data": ideas }

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Obtain profile and reputation information for a given user.

        Args:
            user_id (str): The unique identifier for the user.

        Returns:
            dict:
                - If user exists:
                    { "success": True, "data": UserInfo }
                - If user not found:
                    { "success": False, "error": "User not found" }

        Constraints:
            - user_id must exist in the users storage.
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user }

    def get_comments_for_idea(self, idea_id: str) -> dict:
        """
        Retrieve all comments associated with a specific idea post, organized in threaded (parent/child) structure.

        Args:
            idea_id (str): The UUID of the idea post.

        Returns:
            dict:
                - If idea exists:
                    { "success": True, "data": [ <threaded comments tree> ] }
                - If idea_id invalid:
                    { "success": False, "error": "Idea not found" }

        Constraints:
            - idea_id must exist
            - Threaded replies are nested recursively via 'replies' field.
        """
        if idea_id not in self.ideas:
            return { "success": False, "error": "Idea not found" }

        # Gather all comments for this idea
        idea_comments = [
            comment for comment in self.comments.values()
            if comment["idea_id"] == idea_id
        ]
        # Build mapping from comment_id to the comment, plus add 'replies' field
        comment_map = {}
        for comment in idea_comments:
            comment_copy = comment.copy()
            comment_copy["replies"] = []
            comment_map[comment["comment_id"]] = comment_copy

        # Organize comments into threaded tree structure
        roots = []  # Top-level comments
        for comment in comment_map.values():
            parent_id = comment["parent_comment_id"]
            if parent_id is None:
                roots.append(comment)
            elif parent_id in comment_map:
                comment_map[parent_id]["replies"].append(comment)
            # else: parent missing, ignore (shouldn't happen if constraints hold)

        return { "success": True, "data": roots }

    def get_comment_by_id(self, comment_id: str) -> dict:
        """
        Retrieve the details of a specific comment using its comment_id.

        Args:
            comment_id (str): The UUID of the comment to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": CommentInfo  # Details of the found comment
            }
            or
            {
                "success": False,
                "error": "Comment not found"
            }

        Constraints:
            - comment_id must exist in the system.
        """
        if comment_id not in self.comments:
            return { "success": False, "error": "Comment not found" }
        return { "success": True, "data": self.comments[comment_id] }

    def list_comments_by_user(self, user_id: str) -> dict:
        """
        List all comments authored by a specific user across the platform.

        Args:
            user_id (str): The user's unique identifier.

        Returns:
            dict: {
                "success": True,
                "data": List[CommentInfo],  # List of comments authored by the user, may be empty if none found
            }
            or
            {
                "success": False,
                "error": str  # Description of the error if user does not exist
            }

        Constraints:
            - User with user_id must exist in the system.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        user_comments = [
            comment for comment in self.comments.values()
            if comment["author_id"] == user_id
        ]

        return {"success": True, "data": user_comments}

    def get_votes_for_target(self, target_type: str, target_id: str) -> dict:
        """
        Retrieve all vote records (VoteInfo) for a given idea or comment.

        Args:
            target_type (str): "idea" or "comment"
            target_id (str): UUID of the idea or comment

        Returns:
            dict: {
                "success": True,
                "data": List[VoteInfo],  # List of votes (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Error description
            }
        Constraints:
            - target_type must be either "idea" or "comment".
            - target_id must exist for the respective type.
        """

        # Check target_type validity
        if target_type not in ("idea", "comment"):
            return {"success": False, "error": "Invalid target_type. Must be 'idea' or 'comment'."}

        # Check the target exists
        if target_type == "idea":
            if target_id not in self.ideas:
                return {"success": False, "error": "Idea with given target_id does not exist."}
        elif target_type == "comment":
            if target_id not in self.comments:
                return {"success": False, "error": "Comment with given target_id does not exist."}

        # Gather votes for target
        votes = [
            vote_info for vote_info in self.votes.values()
            if vote_info["target_type"] == target_type and vote_info["target_id"] == target_id
        ]
        return {"success": True, "data": votes}

    def has_user_voted(self, user_id: str, target_type: str, target_id: str) -> dict:
        """
        Check whether a user has already voted on a specific target (idea or comment).

        Args:
            user_id (str): The ID of the user.
            target_type (str): Either 'idea' or 'comment'.
            target_id (str): The ID of the idea or comment.

        Returns:
            dict: {
                "success": True,
                "data": bool,  # True if user has already voted; else False
            }
            or
            {
                "success": False,
                "error": str  # Reason for error, such as invalid target_type
            }

        Constraints:
            - target_type must be 'idea' or 'comment'.
            - Only one vote per user/target combination should exist.
        """
        if target_type not in {'idea', 'comment'}:
            return { "success": False, "error": "Invalid target_type" }

        for vote in self.votes.values():
            if (
                vote['voter_id'] == user_id and
                vote['target_type'] == target_type and
                vote['target_id'] == target_id
            ):
                return { "success": True, "data": True }

        return { "success": True, "data": False }

    def get_vote_count(self, target_type: str, target_id: str) -> dict:
        """
        Get aggregate vote count (sum of vote_value) for the given idea or comment.

        Args:
            target_type (str): Either 'idea' or 'comment'
            target_id (str): The UUID of the idea or comment.

        Returns:
            dict:
                success (bool): True if the vote count is retrieved, False otherwise.
                data (int): The aggregate vote count (only if success=True).
                error (str): Error message describing the failure (only if success=False).

        Constraints:
            - target_type must be 'idea' or 'comment'.
            - The target (idea or comment) must exist.

        Notes:
            - If there are no votes for the target, the count is 0 (still successful).
        """
        if target_type not in ('idea', 'comment'):
            return { "success": False, "error": "Invalid target_type (must be 'idea' or 'comment')." }

        if target_type == 'idea':
            if target_id not in self.ideas:
                return { "success": False, "error": "Idea with the given ID does not exist." }
        else:  # 'comment'
            if target_id not in self.comments:
                return { "success": False, "error": "Comment with the given ID does not exist." }

        vote_sum = sum(
            vote['vote_value']
            for vote in self.votes.values()
            if vote['target_type'] == target_type and vote['target_id'] == target_id
        )

        return { "success": True, "data": vote_sum }

    def create_idea(
        self,
        idea_id: str,
        author_id: str,
        content: str,
        timestamp: str,
        visibility: str,
        tags: list
    ) -> dict:
        """
        Add a new trading idea post for a user. Enforces:
          - idea_id must be unique in the system.
          - author_id must correspond to an existing user.

        Args:
            idea_id (str): Unique identifier (UUID) of the idea.
            author_id (str): User ID of the idea's author.
            content (str): Content of the trading idea.
            timestamp (str): When the idea is posted.
            visibility (str): Visibility status (e.g. "public", "private").
            tags (list): List of tags/labels for the idea.

        Returns:
            dict: {
                "success": True,
                "message": "Idea created successfully"
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
          - idea_id must be unique.
          - author_id must exist in the system.
        """
        if idea_id in self.ideas:
            return {"success": False, "error": "Idea ID already exists"}
        if author_id not in self.users:
            return {"success": False, "error": "Author does not exist"}
        # Construct IdeaPostInfo (vote_count initialized to 0)
        idea_info = {
            "idea_id": idea_id,
            "author_id": author_id,
            "content": content,
            "timestamp": timestamp,
            "visibility": visibility,
            "tags": tags,
            "vote_count": 0
        }
        self.ideas[idea_id] = idea_info
        return {"success": True, "message": "Idea created successfully"}

    def update_idea(
        self,
        idea_id: str,
        author_id: str,
        content: Optional[str] = None,
        tags: Optional[List[str]] = None,
        visibility: Optional[str] = None
    ) -> dict:
        """
        Edit the content, tags, and/or visibility of an existing idea post.

        Args:
            idea_id (str): The UUID of the idea post to update.
            author_id (str): The user ID attempting the update (must be the post's author).
            content (Optional[str]): New content for the idea post.
            tags (Optional[List[str]]): New tags for the idea post.
            visibility (Optional[str]): New visibility status for the idea post.

        Returns:
            dict: {
                "success": True,
                "message": "Idea updated"
            }
            or
            {
                "success": False,
                "error": <reason>
            }
    
        Constraints:
            - The idea post must exist.
            - Only the post's author can update it.
            - At least one updatable field (content, tags, visibility) must be provided.
        """
        # Check if the idea exists
        idea = self.ideas.get(idea_id)
        if not idea:
            return { "success": False, "error": "Idea does not exist." }
    
        # Check if the user is the author
        if idea["author_id"] != author_id:
            return { "success": False, "error": "Permission denied: Only the author can update this idea." }

        # Track if any field is updated
        fields_updated = False

        if content is not None:
            idea["content"] = content
            fields_updated = True
        if tags is not None:
            idea["tags"] = tags
            fields_updated = True
        if visibility is not None:
            idea["visibility"] = visibility
            fields_updated = True

        if not fields_updated:
            return { "success": False, "error": "No update fields provided." }

        # Optionally: update a "modified" timestamp if such a field exists (not in current model)

        self.ideas[idea_id] = idea  # Update dict for explicitness

        return { "success": True, "message": "Idea updated" }

    def delete_idea(self, idea_id: str) -> dict:
        """
        Remove an idea post and handle cascading removal of associated comments and votes.

        Args:
            idea_id (str): The UUID of the idea to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Idea and all associated comments and votes deleted."
            }
            or
            {
                "success": False,
                "error": str  # Explanation if the idea does not exist
            }

        Constraints:
            - Idea must exist.
            - All comments linked to this idea (by idea_id) are deleted.
            - All votes linked to this idea (target_type 'idea', target_id == idea_id) are deleted.
            - All votes on comments linked to this idea are also deleted.
        """
        if idea_id not in self.ideas:
            return { "success": False, "error": "Idea does not exist." }

        # Delete the idea post
        del self.ideas[idea_id]

        # Find all comment_ids associated with this idea (any parent/child in the thread)
        comments_to_delete = [cid for cid, cinfo in self.comments.items() if cinfo["idea_id"] == idea_id]

        # Remove relevant comments
        for comment_id in comments_to_delete:
            del self.comments[comment_id]

        # Find all vote_ids to delete for the idea and its comments
        vote_ids_to_delete = []
        for vote_id, vote in self.votes.items():
            if (
                (vote["target_type"] == "idea" and vote["target_id"] == idea_id)
                or
                (vote["target_type"] == "comment" and vote["target_id"] in comments_to_delete)
            ):
                vote_ids_to_delete.append(vote_id)
        for vote_id in vote_ids_to_delete:
            del self.votes[vote_id]

        return {
            "success": True,
            "message": "Idea and all associated comments and votes deleted."
        }

    def create_comment(
        self,
        comment_id: str,
        idea_id: str,
        author_id: str,
        content: str,
        timestamp: str,
        parent_comment_id: Optional[str] = None
    ) -> dict:
        """
        Add a new comment to an idea post or as a reply to another comment.
    
        Args:
            comment_id (str): Unique UUID for this comment (must be unused).
            idea_id (str): Target idea's UUID (must exist).
            author_id (str): User ID of comment author (must exist).
            content (str): The body of the comment.
            timestamp (str): Timestamp for comment creation (ISO8601 or platform standard).
            parent_comment_id (Optional[str]): If reply, the parent comment's UUID, else None.

        Returns:
            dict:
                On success: { "success": True, "message": "Comment created successfully." }
                On failure: { "success": False, "error": <error_reason> }
    
        Constraints:
            - comment_id must be unique within the system.
            - idea_id must exist in ideas.
            - author_id must exist in users.
            - If parent_comment_id is not None: it must exist in comments and have the same idea_id as the new comment (i.e., threading within an idea only).
        """
        # comment_id unique check
        if comment_id in self.comments:
            return { "success": False, "error": "Comment ID already exists." }

        # idea_id exists
        if idea_id not in self.ideas:
            return { "success": False, "error": "Target idea does not exist." }

        # author exists
        if author_id not in self.users:
            return { "success": False, "error": "Author user does not exist." }

        # parent_comment_id check
        if parent_comment_id is not None:
            if parent_comment_id not in self.comments:
                return { "success": False, "error": "Parent comment does not exist." }
            if self.comments[parent_comment_id]["idea_id"] != idea_id:
                return { "success": False, "error": "Parent comment belongs to different idea." }

        # Construct comment info
        new_comment = {
            "comment_id": comment_id,
            "idea_id": idea_id,
            "author_id": author_id,
            "content": content,
            "timestamp": timestamp,
            "parent_comment_id": parent_comment_id,
            "vote_count": 0
        }

        self.comments[comment_id] = new_comment

        return { "success": True, "message": "Comment created successfully." }

    def update_comment(self, comment_id: str, new_content: str) -> dict:
        """
        Edit the content of an existing comment.
    
        Args:
            comment_id (str): The comment's unique identifier (UUID).
            new_content (str): The new content to replace the old comment's content.
    
        Returns:
            dict: {
                "success": True,
                "message": "Comment updated"
            }
            or
            {
                "success": False,
                "error": str  # "Comment not found"
            }
    
        Constraints:
            - The comment must exist.
            - (Optionally) Only the author should be able to edit.
            - The timestamp should be updated to the current time.
        """

        comment = self.comments.get(comment_id)
        if not comment:
            return {"success": False, "error": "Comment not found"}
    
        comment["content"] = new_content
        # Update the timestamp to ISO format now
        comment["timestamp"] = datetime.utcnow().isoformat() + "Z"

        return {"success": True, "message": "Comment updated"}

    def delete_comment(self, comment_id: str) -> dict:
        """
        Remove a comment, recursively deleting all its reply comments (cascade) and all votes 
        associated with the comment or any reply-descendant.

        Args:
            comment_id (str): The UUID of the comment to be deleted.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Comment and associated replies/votes deleted." }
                - On error:   { "success": False, "error": "<reason>" }

        Constraints:
            - The provided comment_id must exist.
            - All direct and nested reply comments, and all associated votes, must be deleted (cascade).
        """
        if comment_id not in self.comments:
            return { "success": False, "error": "Comment does not exist." }

        # Helper: recursively collect all descendant comment_ids (including root)
        def collect_descendant_comment_ids(cid: str) -> list:
            descendants = [cid]
            for c in self.comments.values():
                if c['parent_comment_id'] == cid:
                    descendants.extend(collect_descendant_comment_ids(c['comment_id']))
            return descendants

        # Step 1: Gather all comments to delete (root + all replies)
        comment_ids_to_delete = collect_descendant_comment_ids(comment_id)

        # Step 2: Delete votes associated with these comments
        target_comment_ids_set = set(comment_ids_to_delete)
        votes_to_delete = [vid for vid, v in self.votes.items()
                           if v['target_type'] == 'comment' and v['target_id'] in target_comment_ids_set]
        for vid in votes_to_delete:
            del self.votes[vid]

        # Step 3: Delete all comments in list
        for cid in comment_ids_to_delete:
            if cid in self.comments:
                del self.comments[cid]

        return { "success": True, "message": "Comment and associated replies/votes deleted." }


    def cast_vote(
        self,
        voter_id: str,
        target_type: str,
        target_id: str,
        vote_value: int,
        timestamp: str
    ) -> dict:
        """
        Create a new vote from a user on an idea or comment, ensuring no duplicate voting.

        Args:
            voter_id (str): User ID of the voter.
            target_type (str): 'idea' or 'comment'.
            target_id (str): UUID of the post or comment.
            vote_value (int): The value of the vote (typically 1 or -1).
            timestamp (str): Timestamp of the vote.

        Returns:
            dict:
                - On success: { "success": True, "message": "Vote cast successfully" }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - voter_id must exist in users.
            - target_type must be 'idea' or 'comment'; the corresponding target_id must exist.
            - The user cannot vote more than once on the same target.
            - Updates vote_count on the target.
        """
        # Validate user exists
        if voter_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        # Validate target_type and target existence
        if target_type == "idea":
            if target_id not in self.ideas:
                return { "success": False, "error": "Idea post does not exist" }
        elif target_type == "comment":
            if target_id not in self.comments:
                return { "success": False, "error": "Comment does not exist" }
        else:
            return { "success": False, "error": "Invalid target_type (must be 'idea' or 'comment')" }
    
        # Check for duplicate vote
        for vote in self.votes.values():
            if vote["voter_id"] == voter_id and vote["target_type"] == target_type and vote["target_id"] == target_id:
                return { "success": False, "error": "User has already voted on this target" }
    
        # All checks passed, create the vote
        vote_id = str(uuid.uuid4())
        self.votes[vote_id] = {
            "vote_id": vote_id,
            "voter_id": voter_id,
            "target_type": target_type,
            "target_id": target_id,
            "vote_value": vote_value,
            "timestamp": timestamp
        }

        # Update vote_count on the target
        if target_type == "idea":
            self.ideas[target_id]["vote_count"] += vote_value
        else:
            self.comments[target_id]["vote_count"] += vote_value

        return { "success": True, "message": "Vote cast successfully" }

    def update_vote(self, vote_id: str, new_vote_value: int) -> dict:
        """
        Change the value of an existing vote.
    
        Args:
            vote_id (str): UUID of the vote to update.
            new_vote_value (int): The new vote value (e.g., 1 or -1).
        
        Returns:
            dict: 
                - On success: { "success": True, "message": "Vote updated." }
                - On failure: { "success": False, "error": "<reason>" }
    
        Constraints:
            - The vote must exist.
            - The change must update the vote_count on the associated idea/comment.
            - The target (idea or comment) must exist.
        """

        # Check if vote exists
        if vote_id not in self.votes:
            return { "success": False, "error": "Vote does not exist." }

        vote = self.votes[vote_id]
        old_vote_value = vote['vote_value']
        if old_vote_value == new_vote_value:
            return { "success": True, "message": "No change needed (same vote value)." }
    
        # Identify and check target existence
        target_type = vote['target_type']
        target_id = vote['target_id']
        if target_type == "idea":
            if target_id not in self.ideas:
                return { "success": False, "error": "Target idea does not exist." }
            # Adjust vote count on the idea
            self.ideas[target_id]['vote_count'] += (new_vote_value - old_vote_value)
        elif target_type == "comment":
            if target_id not in self.comments:
                return { "success": False, "error": "Target comment does not exist." }
            # Adjust vote count on the comment
            self.comments[target_id]['vote_count'] += (new_vote_value - old_vote_value)
        else:
            return { "success": False, "error": "Invalid vote target type." }
    
        # Update the vote value and timestamp
        vote['vote_value'] = new_vote_value
        vote['timestamp'] = str(time.time())
        self.votes[vote_id] = vote

        return { "success": True, "message": "Vote updated." }

    def delete_vote(self, vote_id: str) -> dict:
        """
        Remove a vote (by vote_id) from the system, and update the corresponding idea or comment's vote count.

        Args:
            vote_id (str): The unique identifier of the vote to be deleted.

        Returns:
            dict: 
            - On success: { "success": True, "message": "Vote deleted successfully." }
            - On failure (not found): { "success": False, "error": "Vote not found." }

        Constraints:
            - If the vote is found, it is removed.
            - The corresponding target's vote_count is decremented.
            - If the target (idea/comment) no longer exists, finish without error.
        """
        if vote_id not in self.votes:
            return {"success": False, "error": "Vote not found."}

        vote = self.votes[vote_id]
        target_type = vote["target_type"]
        target_id = vote["target_id"]
        vote_value = vote["vote_value"]

        # Remove the vote from the system
        del self.votes[vote_id]

        # Update the corresponding target's vote count, if it exists
        if target_type == "idea":
            if target_id in self.ideas:
                self.ideas[target_id]["vote_count"] -= vote_value
                # Optional: Clamp to zero if negative
                if self.ideas[target_id]["vote_count"] < 0:
                    self.ideas[target_id]["vote_count"] = 0
        elif target_type == "comment":
            if target_id in self.comments:
                self.comments[target_id]["vote_count"] -= vote_value
                if self.comments[target_id]["vote_count"] < 0:
                    self.comments[target_id]["vote_count"] = 0
        # If target is missing, just skip adjustment

        return {"success": True, "message": "Vote deleted successfully."}

    def delete_user(self, user_id: str) -> dict:
        """
        Remove a user and cascade delete or anonymize their authored ideas, comments, and votes.

        Args:
            user_id (str): The unique identifier of the user to delete.

        Returns:
            dict:
                On success: { "success": True, "message": "User and associated data deleted (cascade)." }
                On error: { "success": False, "error": "User does not exist" }

        Constraints:
            - Removes all ideas, comments, and votes authored by the user (cascade).
            - Deleting an idea cascades to remove associated comments and votes.
            - Deleting a comment also recursively removes replies and associated votes.
            - All votes cast by this user are deleted.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        # Utility: recursively delete all comments (and their replies) by comment_id
        def recursive_delete_comment(comment_id: str):
            # Delete votes on this comment
            votes_to_delete = [vid for vid, v in self.votes.items()
                               if v['target_type'] == 'comment' and v['target_id'] == comment_id]
            for vid in votes_to_delete:
                del self.votes[vid]
            # Delete replies to this comment (recursive)
            replies = [cid for cid, c in self.comments.items() if c['parent_comment_id'] == comment_id]
            for reply_id in replies:
                recursive_delete_comment(reply_id)
            # Delete the comment itself
            if comment_id in self.comments:
                del self.comments[comment_id]

        # 1. Delete all ideas authored by this user (with cascade)
        ideas_to_delete = [iid for iid, idea in self.ideas.items() if idea['author_id'] == user_id]
        for idea_id in ideas_to_delete:
            # Delete all votes on the idea
            votes_on_idea = [vid for vid, v in self.votes.items()
                             if v['target_type'] == 'idea' and v['target_id'] == idea_id]
            for vid in votes_on_idea:
                del self.votes[vid]
            # Delete all comments (and their threads) for this idea
            comments_on_idea = [cid for cid, c in self.comments.items() if c['idea_id'] == idea_id and c['parent_comment_id'] is None]
            for comment_id in comments_on_idea:
                recursive_delete_comment(comment_id)
            # Delete the idea itself
            del self.ideas[idea_id]

        # 2. Delete all comments authored by this user (including threaded replies)
        user_comment_ids = [cid for cid, c in self.comments.items() if c['author_id'] == user_id]
        for comment_id in user_comment_ids:
            recursive_delete_comment(comment_id)

        # 3. Delete all votes cast by this user
        votes_by_user = [vid for vid, v in self.votes.items() if v['voter_id'] == user_id]
        for vid in votes_by_user:
            del self.votes[vid]

        # 4. Finally, remove the user
        del self.users[user_id]

        return { "success": True, "message": "User and associated data deleted (cascade)." }

    def update_user_profile(
        self,
        user_id: str,
        profile_info: Optional[str] = None,
        reputation: Optional[int] = None
    ) -> dict:
        """
        Edit a user's profile information and/or reputation.
    
        Args:
            user_id (str): ID of the user to update.
            profile_info (Optional[str]): New profile info (if updating).
            reputation (Optional[int]): New reputation score (if updating).
        
        Returns:
            dict: {
                "success": True,
                "message": "User profile information updated."
            }
            or
            {
                "success": False,
                "error": "reason for failure"
            }
    
        Constraints:
            - User must exist in the system.
            - At least one of 'profile_info' or 'reputation' must be provided.
            - If 'reputation' is provided, it must be of int type.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist." }

        if profile_info is None and reputation is None:
            return { "success": False, "error": "No update parameters provided (profile_info and/or reputation required)." }
    
        updated = False
        if profile_info is not None:
            self.users[user_id]["profile_info"] = profile_info
            updated = True
    
        if reputation is not None:
            if not isinstance(reputation, int):
                return { "success": False, "error": "Reputation must be an integer." }
            self.users[user_id]["reputation"] = reputation
            updated = True

        if updated:
            return { "success": True, "message": "User profile information updated." }
        else:
            return { "success": False, "error": "No changes were made to the user profile." }


class TradingPlatformBackend(BaseEnv):
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
            normalized = copy.deepcopy(value)
            if key == "comments" and isinstance(normalized, dict):
                for comment in normalized.values():
                    if isinstance(comment, dict) and comment.get("parent_comment_id", None) == "":
                        comment["parent_comment_id"] = None
            setattr(env, key, normalized)

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

    def get_idea_by_id(self, **kwargs):
        return self._call_inner_tool('get_idea_by_id', kwargs)

    def list_ideas_by_user(self, **kwargs):
        return self._call_inner_tool('list_ideas_by_user', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def get_comments_for_idea(self, **kwargs):
        return self._call_inner_tool('get_comments_for_idea', kwargs)

    def get_comment_by_id(self, **kwargs):
        return self._call_inner_tool('get_comment_by_id', kwargs)

    def list_comments_by_user(self, **kwargs):
        return self._call_inner_tool('list_comments_by_user', kwargs)

    def get_votes_for_target(self, **kwargs):
        return self._call_inner_tool('get_votes_for_target', kwargs)

    def has_user_voted(self, **kwargs):
        return self._call_inner_tool('has_user_voted', kwargs)

    def get_vote_count(self, **kwargs):
        return self._call_inner_tool('get_vote_count', kwargs)

    def create_idea(self, **kwargs):
        return self._call_inner_tool('create_idea', kwargs)

    def update_idea(self, **kwargs):
        return self._call_inner_tool('update_idea', kwargs)

    def delete_idea(self, **kwargs):
        return self._call_inner_tool('delete_idea', kwargs)

    def create_comment(self, **kwargs):
        return self._call_inner_tool('create_comment', kwargs)

    def update_comment(self, **kwargs):
        return self._call_inner_tool('update_comment', kwargs)

    def delete_comment(self, **kwargs):
        return self._call_inner_tool('delete_comment', kwargs)

    def cast_vote(self, **kwargs):
        return self._call_inner_tool('cast_vote', kwargs)

    def update_vote(self, **kwargs):
        return self._call_inner_tool('update_vote', kwargs)

    def delete_vote(self, **kwargs):
        return self._call_inner_tool('delete_vote', kwargs)

    def delete_user(self, **kwargs):
        return self._call_inner_tool('delete_user', kwargs)

    def update_user_profile(self, **kwargs):
        return self._call_inner_tool('update_user_profile', kwargs)
