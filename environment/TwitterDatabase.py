# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Optional



class EngagementStats(TypedDict):
    likes: int
    retweets: int
    replies: int

class TweetInfo(TypedDict):
    tweet_id: str
    author_id: str
    content: str
    timestamp: str
    engagement_stats: EngagementStats
    in_reply_to_status_id: Optional[str]
    media_attachment: Optional[str]

class UserInfo(TypedDict):
    user_id: str
    username: str
    display_name: str
    account_created_at: str
    profile_info: str
    is_verified: bool
    status: str  # e.g., 'active', 'suspended'

class RelationshipInfo(TypedDict):
    follower_id: str
    followee_id: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Twitter database system environment.
        """

        # Tweets: {tweet_id: TweetInfo}
        self.tweets: Dict[str, TweetInfo] = {}
        # (entity: Tweet; attributes: tweet_id, author_id, content, timestamp, engagement_stats, in_reply_to_status_id, media_attachment)

        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}
        # (entity: User; attributes: user_id, username, display_name, account_created_at, profile_info, is_verified, status)

        # Relationships: List of RelationshipInfo (follower_id follows followee_id)
        self.relationships: List[RelationshipInfo] = []
        # (entity: Relationship; attributes: follower_id, followee_id)

        # Constraints:
        # - Each tweet must have a valid author_id referencing an existing User.
        # - tweet_id values are unique across all tweets.
        # - follower_id and followee_id in Relationship must reference existing users.
        # - Engagement statistics (likes, retweets, replies) are non-negative integers.

    def get_tweet_by_id(self, tweet_id: str) -> dict:
        """
        Retrieve the full details of a single tweet given its tweet_id.

        Args:
            tweet_id (str): The unique ID of the tweet to query.

        Returns:
            dict:
                On success:
                    { "success": True, "data": TweetInfo }
                On failure:
                    { "success": False, "error": "Tweet not found" }

        Constraints:
            - The tweet_id must exist in the database.
        """
        tweet = self.tweets.get(tweet_id)
        if tweet is None:
            return { "success": False, "error": "Tweet not found" }
        return { "success": True, "data": tweet }

    def get_tweets_by_ids(self, tweet_ids: list) -> dict:
        """
        Retrieve full details for a list of tweets specified by their tweet_ids.

        Args:
            tweet_ids (list of str): The tweet IDs to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": List[TweetInfo],  # List of tweet details found for the provided IDs.
            }
            or
            {
                "success": False,
                "error": str  # Problem description, e.g. no valid tweet_ids found or invalid input.
            }

        Constraints:
            - tweet_id values are unique across all tweets.
            - Valid tweet_ids must exist in the database.
        """
        if not isinstance(tweet_ids, list):
            return {"success": False, "error": "Input tweet_ids must be a list."}
        if not all(isinstance(tid, str) for tid in tweet_ids):
            return {"success": False, "error": "All tweet_ids must be strings."}

        found_tweets = []
        for tid in tweet_ids:
            if tid in self.tweets:
                found_tweets.append(self.tweets[tid])

        if not found_tweets:
            return {"success": False, "error": "No valid tweet_ids found."}

        return {"success": True, "data": found_tweets}

    def get_tweets_by_author(self, user_id: str) -> dict:
        """
        Retrieve all tweets authored by the specified user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": List[TweetInfo]  # List of tweets authored by the user (possibly empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g. user does not exist)
            }

        Constraints:
            - user_id must exist in the database.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        tweets_by_author = [
            tweet for tweet in self.tweets.values()
            if tweet["author_id"] == user_id
        ]

        return { "success": True, "data": tweets_by_author }

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user information for a given user_id.

        Args:
            user_id (str): The unique identifier of the user to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo  # User metadata if found
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g. 'User not found'
            }

        Constraints:
            - user_id must exist in the system.
        """
        user_info = self.users.get(user_id)
        if user_info is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user_info }

    def get_user_by_username(self, username: str) -> dict:
        """
        Retrieve user information for a user by their username.

        Args:
            username (str): The username to search for.

        Returns:
            dict:
                {
                    "success": True,
                    "data": UserInfo,  # full user information if found
                }
                or
                {
                    "success": False,
                    "error": str,  # reason user was not found
                }

        Constraints:
            - Usernames are unique in the system.
        """
        for user_info in self.users.values():
            if user_info["username"] == username:
                return {"success": True, "data": user_info}

        return {"success": False, "error": "User not found"}

    def get_followers(self, user_id: str) -> dict:
        """
        Retrieve the list of user_ids who follow the specified user.

        Args:
            user_id (str): The user_id of the user to retrieve followers for.

        Returns:
            dict: {
                "success": True,
                "data": List[str],  # list of follower_ids (may be empty if no followers)
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g., "User does not exist"
            }

        Constraints:
            - user_id must reference an existing User.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        followers = [
            rel['follower_id']
            for rel in self.relationships
            if rel['followee_id'] == user_id and rel['follower_id'] in self.users
        ]

        return { "success": True, "data": followers }

    def get_followees(self, user_id: str) -> dict:
        """
        Retrieve the list of user_ids that the specified user (user_id) is following.

        Args:
            user_id (str): The user ID of the follower.

        Returns:
            dict: {
                "success": True,
                "data": List[str]  # List of followee user_ids (could be empty if not following anyone)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., user does not exist)
            }

        Constraints:
          - user_id must reference an existing user.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        followees = [
            rel["followee_id"]
            for rel in self.relationships
            if rel["follower_id"] == user_id
        ]

        return { "success": True, "data": followees }

    def check_user_relationship(self, follower_id: str, followee_id: str) -> dict:
        """
        Determine if a user (follower_id) follows another user (followee_id).

        Args:
            follower_id (str): The user_id of the follower.
            followee_id (str): The user_id of the followee.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": bool  # True if follower follows followee, False otherwise
                    }
                On error:
                    {
                        "success": False,
                        "error": str  # Description of error (e.g., user not found)
                    }

        Constraints:
            - Both follower_id and followee_id must reference existing users.
        """
        if follower_id not in self.users:
            return { "success": False, "error": f"Follower user_id '{follower_id}' does not exist." }
        if followee_id not in self.users:
            return { "success": False, "error": f"Followee user_id '{followee_id}' does not exist." }
    
        exists = any(
            rel['follower_id'] == follower_id and rel['followee_id'] == followee_id
            for rel in self.relationships
        )
        return { "success": True, "data": exists }

    def get_engagement_stats(self, tweet_id: str) -> dict:
        """
        Return engagement statistics (likes, retweets, replies) for a given tweet.

        Args:
            tweet_id (str): The ID of the tweet.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "likes": int,
                    "retweets": int,
                    "replies": int
                }
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (e.g., tweet does not exist)
            }

        Constraints:
            - tweet_id must refer to an existing tweet.
            - Engagement statistics are non-negative integers.
        """
        tweet_info = self.tweets.get(tweet_id)
        if tweet_info is None:
            return {"success": False, "error": "Tweet does not exist"}

        stats = tweet_info["engagement_stats"]
        return {
            "success": True,
            "data": {
                "likes": stats["likes"],
                "retweets": stats["retweets"],
                "replies": stats["replies"]
            }
        }

    def get_tweet_thread(self, tweet_id: str) -> dict:
        """
        Retrieve the full conversation thread associated with a given tweet_id,
        including the root tweet, the queried tweet, and all descendant replies
        that belong to the same conversation tree.

        Args:
            tweet_id (str): The tweet whose thread is requested.

        Returns:
            dict: {
                "success": True,
                "data": List[TweetInfo],  # List of tweets in the conversation tree, ordered chronologically from the root thread
            }
            or
            {
                "success": False,
                "error": str  # Description, e.g. tweet not found
            }

        Constraints:
            - The given tweet_id must exist in the database.
            - Each ancestor tweet referenced by in_reply_to_status_id must exist. Traversal stops at first missing ancestor.
            - If descendant replies exist under the same conversation root, they are included in the returned thread data.
        """
        queried_tweet = self.tweets.get(tweet_id)
        if queried_tweet is None:
            return { "success": False, "error": "Tweet not found" }

        # Walk up to find the conversation root.
        root_id = tweet_id
        visited: set[str] = set()
        current_id: str = tweet_id
        while current_id:
            if current_id in visited:
                break
            visited.add(current_id)
            tweet_info = self.tweets.get(current_id)
            if tweet_info is None:
                break
            root_id = current_id
            parent_id = tweet_info.get("in_reply_to_status_id")
            if not parent_id:
                break
            current_id = parent_id

        # Collect the entire descendant tree starting from the root.
        collected_ids: set[str] = set()
        queue: list[str] = [root_id]
        while queue:
            current = queue.pop(0)
            if current in collected_ids:
                continue
            tweet_info = self.tweets.get(current)
            if tweet_info is None:
                continue
            collected_ids.add(current)
            children = [
                child_id
                for child_id, child_tweet in self.tweets.items()
                if child_tweet.get("in_reply_to_status_id") == current
            ]
            children.sort(key=lambda child_id: self.tweets[child_id].get("timestamp", ""))
            queue.extend(children)

        thread = [self.tweets[tid] for tid in collected_ids]
        thread.sort(key=lambda tweet: tweet.get("timestamp", ""))

        return { "success": True, "data": thread }

    def list_all_users(self) -> dict:
        """
        Retrieve a list of all users in the database.

        Returns:
            dict: {
                "success": True,
                "data": List[UserInfo]  # List of all users (could be empty if no users exist)
            }

        Constraints/Notes:
            - No input parameters.
            - If no users exist, returns success with an empty list.
            - Does NOT perform any status (active/suspended) checks.
        """
        user_list = list(self.users.values())
        return {
            "success": True,
            "data": user_list
        }

    def list_all_tweets(self) -> dict:
        """
        Retrieve all tweets in the database.

        Returns:
            dict: {
                "success": True,
                "data": List[TweetInfo]  # List of all tweet info dictionaries (may be empty if no tweets)
            }
        """
        all_tweets = list(self.tweets.values())
        return {"success": True, "data": all_tweets}

    def add_new_tweet(
        self,
        tweet_id: str,
        author_id: str,
        content: str,
        timestamp: str,
        engagement_stats: dict,
        in_reply_to_status_id: Optional[str] = None,
        media_attachment: Optional[str] = None
    ) -> dict:
        """
        Add a new tweet to the database, enforcing constraints:
          - tweet_id must be unique
          - author_id must exist as a user
          - engagement_stats must have non-negative integers for 'likes', 'retweets', 'replies'
          - All fields required except in_reply_to_status_id and media_attachment (optional)
    
        Args:
            tweet_id (str): Unique identifier for the tweet.
            author_id (str): User ID of the author (must exist in users).
            content (str): Text/content of the tweet.
            timestamp (str): Timestamp of tweet creation.
            engagement_stats (dict): {'likes': int, 'retweets': int, 'replies': int}, all non-negative
            in_reply_to_status_id (Optional[str]): If reply, id of parent tweet.
            media_attachment (Optional[str]): Any media info/attachment.

        Returns:
            dict: Success or error message as described above.
        """
        # Check tweet_id uniqueness
        if tweet_id in self.tweets:
            return {"success": False, "error": "Tweet ID already exists."}
        # Check author_id exists
        if author_id not in self.users:
            return {"success": False, "error": "Author ID does not exist."}
        # Check engagement_stats are valid
        required_stats = ('likes', 'retweets', 'replies')
        for stat in required_stats:
            if stat not in engagement_stats:
                return {"success": False, "error": f"Engagement stat '{stat}' is missing."}
            if not isinstance(engagement_stats[stat], int) or engagement_stats[stat] < 0:
                return {"success": False, "error": f"Engagement stat '{stat}' must be a non-negative integer."}

        # Compose TweetInfo dict
        tweet_info = {
            "tweet_id": tweet_id,
            "author_id": author_id,
            "content": content,
            "timestamp": timestamp,
            "engagement_stats": {
                "likes": engagement_stats["likes"],
                "retweets": engagement_stats["retweets"],
                "replies": engagement_stats["replies"]
            },
            "in_reply_to_status_id": in_reply_to_status_id,
            "media_attachment": media_attachment
        }
        self.tweets[tweet_id] = tweet_info

        return {"success": True, "message": "Tweet added successfully"}

    def update_tweet_content(
        self,
        tweet_id: str,
        new_content: Optional[str] = None,
        new_media_attachment: Optional[str] = None
    ) -> dict:
        """
        Update the content and/or media attachment of an existing tweet.

        Args:
            tweet_id (str): ID of the tweet to update.
            new_content (Optional[str]): New content for the tweet. If None, content is unchanged.
            new_media_attachment (Optional[str]): New media attachment. If None, unchanged.

        Returns:
            dict: {
                "success": True,
                "message": "Tweet content/media updated successfully."
            }
            or
            {
                "success": False,
                "error": "Explanation of problem."
            }

        Constraints:
            - tweet_id must reference an existing tweet.
            - At least one of new_content or new_media_attachment must be provided and different from previous.
        """
        tweet = self.tweets.get(tweet_id)
        if tweet is None:
            return { "success": False, "error": "Tweet does not exist." }

        if new_content is None and new_media_attachment is None:
            return { "success": False, "error": "No new content or media attachment provided." }

        updated = False

        if new_content is not None and new_content != tweet["content"]:
            tweet["content"] = new_content
            updated = True

        if new_media_attachment is not None and new_media_attachment != tweet["media_attachment"]:
            tweet["media_attachment"] = new_media_attachment
            updated = True

        if not updated:
            return { "success": False, "error": "No new information to update." }

        # Apply the update in the database
        self.tweets[tweet_id] = tweet  # Not strictly necessary, but makes assignment explicit

        return { "success": True, "message": "Tweet content/media updated successfully." }

    def delete_tweet(self, tweet_id: str) -> dict:
        """
        Remove a tweet from the database.

        Args:
            tweet_id (str): The ID of the tweet to be deleted.

        Returns:
            dict:
                - On success: { "success": True, "message": "Tweet deleted successfully." }
                - On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - The tweet must exist.
            - Cannot delete the tweet if any other tweet replies to it (i.e., where in_reply_to_status_id == tweet_id).
            - tweet_id uniqueness is preserved by the dict data structure.
        """
        # Check tweet exists
        if tweet_id not in self.tweets:
            return { "success": False, "error": "Tweet does not exist." }

        # Check for replies to this tweet
        for t in self.tweets.values():
            if t.get("in_reply_to_status_id") == tweet_id:
                return { "success": False, "error": "Cannot delete tweet with existing replies." }

        # Passed checks -- delete
        del self.tweets[tweet_id]

        return { "success": True, "message": "Tweet deleted successfully." }

    def update_engagement_stats(
        self, 
        tweet_id: str, 
        likes: Optional[int] = None, 
        retweets: Optional[int] = None, 
        replies: Optional[int] = None
    ) -> dict:
        """
        Atomically update the engagement statistics (likes, retweets, replies) for a given tweet.
    
        Args:
            tweet_id (str): The unique identifier of the tweet to update.
            likes (Optional[int]): New number of likes (must be non-negative if provided).
            retweets (Optional[int]): New number of retweets (must be non-negative if provided).
            replies (Optional[int]): New number of replies (must be non-negative if provided).
    
        Returns:
            dict:
                - On success:
                    { "success": True, "message": "Engagement stats updated for tweet <tweet_id>" }
                - On failure:
                    { "success": False, "error": <reason> }
    
        Constraints:
            - Tweet must exist in the database.
            - Engagement stats must be non-negative integers.
            - If no stats are provided, operation is a no-op with a suitable message.
        """
        # Check tweet existence
        tweet = self.tweets.get(tweet_id)
        if tweet is None:
            return { "success": False, "error": "Tweet does not exist" }

        # Check if any stat is being updated
        if likes is None and retweets is None and replies is None:
            return { "success": False, "error": "No engagement statistics provided for update" }

        # Validate stats
        if likes is not None and (not isinstance(likes, int) or likes < 0):
            return { "success": False, "error": "Likes must be a non-negative integer" }
        if retweets is not None and (not isinstance(retweets, int) or retweets < 0):
            return { "success": False, "error": "Retweets must be a non-negative integer" }
        if replies is not None and (not isinstance(replies, int) or replies < 0):
            return { "success": False, "error": "Replies must be a non-negative integer" }

        # Atomically update the stats
        engagement_stats = tweet["engagement_stats"]

        if likes is not None:
            engagement_stats["likes"] = likes
        if retweets is not None:
            engagement_stats["retweets"] = retweets
        if replies is not None:
            engagement_stats["replies"] = replies

        tweet["engagement_stats"] = engagement_stats
        self.tweets[tweet_id] = tweet  # Not strictly needed, dicts are mutable, but for consistency

        return { 
            "success": True, 
            "message": f"Engagement stats updated for tweet {tweet_id}" 
        }

    def add_user(self,
                 user_id: str,
                 username: str,
                 display_name: str,
                 account_created_at: str,
                 profile_info: str,
                 is_verified: bool,
                 status: str) -> dict:
        """
        Add a new user to the user database.

        Args:
            user_id (str): Unique identifier for the user.
            username (str): Unique username.
            display_name (str): Display name for the user.
            account_created_at (str): Account creation timestamp (ISO format).
            profile_info (str): Profile description/info.
            is_verified (bool): Verification status.
            status (str): 'active' or 'suspended'.

        Returns:
            dict: 
                { "success": True, "message": "User added successfully" }
                or
                { "success": False, "error": <error description> }

        Constraints:
            - user_id must be unique; must not already exist in users.
            - username must be unique among all users.
            - status should be 'active' or 'suspended'.
        """
        # Check required fields
        if not all([user_id, username, display_name, account_created_at, profile_info, status]):
            return { "success": False, "error": "Missing required user information" }
        # Check uniqueness of user_id
        if user_id in self.users:
            return { "success": False, "error": "User ID already exists" }
        # Check uniqueness of username
        for existing_user in self.users.values():
            if existing_user["username"] == username:
                return { "success": False, "error": "Username already taken" }
        # Validate status
        if status not in ("active", "suspended"):
            return { "success": False, "error": "Invalid user status" }
        # Create and add user
        new_user: UserInfo = {
            "user_id": user_id,
            "username": username,
            "display_name": display_name,
            "account_created_at": account_created_at,
            "profile_info": profile_info,
            "is_verified": is_verified,
            "status": status
        }
        self.users[user_id] = new_user
        return { "success": True, "message": "User added successfully" }

    def update_user_status(self, user_id: str, new_status: str) -> dict:
        """
        Change a user's status (e.g., set to active or suspended).

        Args:
            user_id (str): The ID of the user to update.
            new_status (str): The new status for the user ('active' or 'suspended').

        Returns:
            dict: {
                "success": True,
                "message": "User status updated successfully."
            }
            or
            {
                "success": False,
                "error": <error message>
            }

        Constraints:
            - user_id must exist in the system.
            - new_status must be one of 'active' or 'suspended'.
        """
        allowed_statuses = ['active', 'suspended']
        user = self.users.get(user_id)
        if user is None:
            return {"success": False, "error": "User does not exist."}
        if new_status not in allowed_statuses:
            return {"success": False, "error": f"Invalid status. Allowed values: {allowed_statuses}"}
        if user["status"] == new_status:
            return {"success": True, "message": f"User status is already {new_status}."}

        user["status"] = new_status
        self.users[user_id] = user
        return {"success": True, "message": "User status updated successfully."}

    def add_relationship(self, follower_id: str, followee_id: str) -> dict:
        """
        Add a new 'follower' relationship from follower_id to followee_id.

        Args:
            follower_id (str): The user_id of the follower.
            followee_id (str): The user_id of the user to be followed.

        Returns:
            dict: {
                "success": True,
                "message": "Relationship added: <follower_id> follows <followee_id>."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Both follower_id and followee_id must refer to existing users.
            - The relationship must not already exist.
            - follower_id cannot be the same as followee_id (no self-follow).
        """
        if follower_id == followee_id:
            return { "success": False, "error": "A user cannot follow themselves." }
        if follower_id not in self.users:
            return { "success": False, "error": f"Follower user_id '{follower_id}' does not exist." }
        if followee_id not in self.users:
            return { "success": False, "error": f"Followee user_id '{followee_id}' does not exist." }
        for rel in self.relationships:
            if rel["follower_id"] == follower_id and rel["followee_id"] == followee_id:
                return { "success": False, "error": "Relationship already exists." }
        # All checks passed, add relationship
        self.relationships.append({"follower_id": follower_id, "followee_id": followee_id})
        return {
            "success": True,
            "message": f"Relationship added: {follower_id} follows {followee_id}."
        }

    def remove_relationship(self, follower_id: str, followee_id: str) -> dict:
        """
        Remove a 'follower' relationship between two users.

        Args:
            follower_id (str): The user ID of the follower.
            followee_id (str): The user ID of the followee.

        Returns:
            dict: On success:
                {"success": True, "message": "Relationship removed: {follower_id} no longer follows {followee_id}"}
            On failure:
                {"success": False, "error": "...reason..."}

        Constraints:
            - Both follower_id and followee_id must reference existing users.
            - Relationship must exist to be removed.
            - No exceptions are raised; errors are returned as dicts.
        """
        if follower_id not in self.users or followee_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        initial_count = len(self.relationships)
        self.relationships = [
            rel for rel in self.relationships
            if not (rel["follower_id"] == follower_id and rel["followee_id"] == followee_id)
        ]
        final_count = len(self.relationships)

        if final_count == initial_count:
            return {"success": False, "error": "Relationship does not exist"}

        return {
            "success": True,
            "message": f"Relationship removed: {follower_id} no longer follows {followee_id}"
        }

    def remove_user(self, user_id: str) -> dict:
        """
        Permanently delete a user (by user_id), and clean up all associated relationships and tweets.

        Args:
            user_id (str): The ID of the user to delete.

        Returns:
            dict:
                success (bool): Operation outcome.
                message (str): Description if successful.
                error (str): Description if failure.
    
        Constraints:
            - User must exist.
            - Remove all tweets authored by this user.
            - Remove all relationships in which this user is follower or followee.
        """
        if user_id not in self.users:
            return {"success": False, "error": f"User '{user_id}' does not exist"}

        # Remove tweets authored by user
        tweets_to_remove = [tid for tid, tinfo in self.tweets.items() if tinfo["author_id"] == user_id]
        for tid in tweets_to_remove:
            del self.tweets[tid]

        # Remove relationships where user is follower or followee
        self.relationships = [
            rel for rel in self.relationships
            if rel["follower_id"] != user_id and rel["followee_id"] != user_id
        ]

        # Remove the user
        del self.users[user_id]

        return {
            "success": True,
            "message": f"User '{user_id}' and all associated tweets and relationships deleted"
        }


class TwitterDatabase(BaseEnv):
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

    def get_tweet_by_id(self, **kwargs):
        return self._call_inner_tool('get_tweet_by_id', kwargs)

    def get_tweets_by_ids(self, **kwargs):
        return self._call_inner_tool('get_tweets_by_ids', kwargs)

    def get_tweets_by_author(self, **kwargs):
        return self._call_inner_tool('get_tweets_by_author', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def get_user_by_username(self, **kwargs):
        return self._call_inner_tool('get_user_by_username', kwargs)

    def get_followers(self, **kwargs):
        return self._call_inner_tool('get_followers', kwargs)

    def get_followees(self, **kwargs):
        return self._call_inner_tool('get_followees', kwargs)

    def check_user_relationship(self, **kwargs):
        return self._call_inner_tool('check_user_relationship', kwargs)

    def get_engagement_stats(self, **kwargs):
        return self._call_inner_tool('get_engagement_stats', kwargs)

    def get_tweet_thread(self, **kwargs):
        return self._call_inner_tool('get_tweet_thread', kwargs)

    def list_all_users(self, **kwargs):
        return self._call_inner_tool('list_all_users', kwargs)

    def list_all_tweets(self, **kwargs):
        return self._call_inner_tool('list_all_tweets', kwargs)

    def add_new_tweet(self, **kwargs):
        return self._call_inner_tool('add_new_tweet', kwargs)

    def update_tweet_content(self, **kwargs):
        return self._call_inner_tool('update_tweet_content', kwargs)

    def delete_tweet(self, **kwargs):
        return self._call_inner_tool('delete_tweet', kwargs)

    def update_engagement_stats(self, **kwargs):
        return self._call_inner_tool('update_engagement_stats', kwargs)

    def add_user(self, **kwargs):
        return self._call_inner_tool('add_user', kwargs)

    def update_user_status(self, **kwargs):
        return self._call_inner_tool('update_user_status', kwargs)

    def add_relationship(self, **kwargs):
        return self._call_inner_tool('add_relationship', kwargs)

    def remove_relationship(self, **kwargs):
        return self._call_inner_tool('remove_relationship', kwargs)

    def remove_user(self, **kwargs):
        return self._call_inner_tool('remove_user', kwargs)
