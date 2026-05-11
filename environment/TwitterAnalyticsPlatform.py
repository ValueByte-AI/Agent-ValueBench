# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
from typing import Optional, List
import time



class TweetInfo(TypedDict):
    # Represents attributes of a Tweet
    tweet_id: str
    user_id: str
    text: str
    timestamp: str
    sentiment_score: float
    favorite_count: int
    retweet_count: int
    reply_count: int
    hashtags: List[str]
    language: str

class UserInfo(TypedDict):
    # Represents attributes of a Twitter user profile
    user_id: str
    username: str
    display_name: str
    profile_image_url: str
    follower_count: int
    following_count: int
    verified_status: bool

class _GeneratedEnvImpl:
    def __init__(self):
        # Tweets: {tweet_id: TweetInfo}
        self.tweets: Dict[str, TweetInfo] = {}

        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Constraints:
        # - Each tweet is associated with exactly one user (via user_id)
        # - Engagement metrics (favorite_count, etc.) are non-negative integers
        # - Sentiment score must be updated if content or analysis algorithm changes
        # - Tweets are searchable/filterable by text, hashtags, user, engagement metrics
        # - User info must be up-to-date for each tweet

    def search_tweets_by_keyword(self, keyword: str) -> dict:
        """
        Retrieve all tweets whose text contains the specified keyword or phrase
        (case-insensitive substring match).

        Args:
            keyword (str): The keyword or phrase to search for.

        Returns:
            dict: {
                "success": True,
                "data": List[TweetInfo],  # Possibly empty list
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Keyword must be a non-empty string.
        """
        if not isinstance(keyword, str) or not keyword.strip():
            return { "success": False, "error": "Keyword must be a non-empty string" }

        keyword_lower = keyword.lower()
        result = [
            tweet for tweet in self.tweets.values()
            if keyword_lower in tweet["text"].lower()
        ]
        return { "success": True, "data": result }

    def search_tweets_by_hashtag(self, hashtag: str) -> dict:
        """
        Retrieve all tweets containing the specified hashtag.

        Args:
            hashtag (str): The hashtag to search for (case-insensitive, without '#' prefix).

        Returns:
            dict: {
                "success": True,
                "data": List[TweetInfo],  # List of tweets containing the hashtag. Empty if none found.
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (e.g., invalid parameter).
            }

        Constraints:
            - Hashtag match is case-insensitive.
            - Will search in each tweet's hashtags list for the provided hashtag.
        """
        if not hashtag or not isinstance(hashtag, str):
            return { "success": False, "error": "Parameter 'hashtag' must be a non-empty string." }

        hashtag_normalized = hashtag.lower().lstrip('#')  # Remove possible '#' and lowercase

        results = []
        for tweet in self.tweets.values():
            # Normalize stored hashtags as well for comparison
            tweet_hashtags_normalized = [h.lower().lstrip('#') for h in tweet.get("hashtags", [])]
            if hashtag_normalized in tweet_hashtags_normalized:
                results.append(tweet)

        return { "success": True, "data": results }

    def filter_tweets_by_engagement(
        self,
        engagement_filters: Dict[str, tuple]
    ) -> dict:
        """
        Retrieve tweets filtered by engagement metrics (favorite_count, retweet_count, reply_count)
        using comparison operators or thresholds.

        Args:
            engagement_filters (Dict[str, tuple]): e.g., {
                "favorite_count": (">=", 10),
                "retweet_count": ("<", 100),
                "reply_count": ("=", 0)
            }
            Supported metrics: "favorite_count", "retweet_count", "reply_count"
            Supported operators: "=", "!=", ">", "<", ">=", "<="

        Returns:
            dict:
                - success: True, data: List[TweetInfo] (may be empty)
                - success: False, error: str

        Constraints:
            - Metrics must be valid and present in TweetInfo.
            - Operators must be supported.
            - No exceptions are raised; errors reported in result dict.
        """
        valid_metrics = {"favorite_count", "retweet_count", "reply_count"}
        valid_operators = {"=", "!=", ">", "<", ">=", "<="}

        if not engagement_filters:
            return {
                "success": False,
                "error": "No engagement filter criteria provided."
            }

        for metric, (operator, threshold) in engagement_filters.items():
            if metric not in valid_metrics:
                return {
                    "success": False,
                    "error": f"Invalid metric '{metric}' provided."
                }
            if operator not in valid_operators:
                return {
                    "success": False,
                    "error": f"Invalid operator '{operator}' for {metric}."
                }
            if not isinstance(threshold, int) or threshold < 0:
                return {
                    "success": False,
                    "error": f"Threshold for {metric} must be a non-negative integer."
                }

        def compare(val: int, operator: str, threshold: int) -> bool:
            if operator == "=":
                return val == threshold
            elif operator == "!=":
                return val != threshold
            elif operator == ">":
                return val > threshold
            elif operator == "<":
                return val < threshold
            elif operator == ">=":
                return val >= threshold
            elif operator == "<=":
                return val <= threshold
            return False  # Should never reach if operator is validated

        result = []
        for tweet in self.tweets.values():
            match = True
            for metric, (operator, threshold) in engagement_filters.items():
                value = tweet.get(metric, None)
                if value is None or not compare(value, operator, threshold):
                    match = False
                    break
            if match:
                result.append(tweet)

        return {
            "success": True,
            "data": result
        }

    def sort_tweets_by_favorite_count(self, order: str) -> dict:
        """
        Sorts and returns all tweets by their favorite_count.

        Args:
            order (str): "desc" for descending or "asc" for ascending sort.

        Returns:
            dict:
                - On success:
                    {
                      "success": True,
                      "data": List[TweetInfo]  # Sorted by favorite_count
                    }
                - On error:
                    {
                      "success": False,
                      "error": str  # Reason for failure
                    }

        Constraints:
            - order must be either "asc" or "desc". Otherwise, returns an error.
            - Empty result is valid if no tweets exist.
        """
        if order not in ("asc", "desc"):
            return {"success": False, "error": "Parameter 'order' must be 'asc' or 'desc'."}

        reverse = (order == "desc")
        tweets_sorted = sorted(
            self.tweets.values(),
            key=lambda t: t["favorite_count"],
            reverse=reverse
        )

        return {"success": True, "data": tweets_sorted}

    def get_user_info_by_tweet(self, tweet_id: str) -> dict:
        """
        Retrieve the user profile (UserInfo) associated with a given tweet by its tweet_id.

        Args:
            tweet_id (str): The ID of the tweet.

        Returns:
            dict:
                { "success": True, "data": UserInfo } on success,
                { "success": False, "error": str } on failure
                    (reasons: tweet not found, associated user not found)

        Constraints:
            - The provided tweet_id must correspond to an existing Tweet.
            - Each tweet is associated with one user (via user_id).
            - The corresponding user profile must exist and be up-to-date.
        """
        # Find the tweet
        tweet = self.tweets.get(tweet_id)
        if not tweet:
            return { "success": False, "error": "Tweet not found" }

        user_id = tweet.get("user_id")
        user_info = self.users.get(user_id)
        if not user_info:
            return { "success": False, "error": "Associated user not found" }

        return { "success": True, "data": user_info }

    def get_user_info_by_user_id(self, user_id: str) -> dict:
        """
        Retrieve the complete user profile information by user_id.

        Args:
            user_id (str): Unique identifier for the user.

        Returns:
            dict: 
                - On success: { "success": True, "data": UserInfo }
                - On failure: { "success": False, "error": "User not found" }

        Constraints:
            - user_id must refer to an existing user in the system.
        """
        user_info = self.users.get(user_id)
        if user_info is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user_info }

    def get_tweet_by_id(self, tweet_id: str) -> dict:
        """
        Retrieve all stored details for a specific tweet by its tweet_id.

        Args:
            tweet_id (str): The identifier of the tweet to retrieve.

        Returns:
            dict: 
                - If tweet found: {"success": True, "data": TweetInfo}
                - If not found: {"success": False, "error": "Tweet not found"}

        Constraints:
            - The tweet_id must exist in the platform.
        """
        tweet_info = self.tweets.get(tweet_id)
        if tweet_info is None:
            return { "success": False, "error": "Tweet not found" }
        return { "success": True, "data": tweet_info }

    def get_tweets_by_user_id(self, user_id: str) -> dict:
        """
        Retrieve all tweets posted by a specific user.

        Args:
            user_id (str): The ID of the user whose tweets will be retrieved.

        Returns:
            dict: {
                "success": True,
                "data": List[TweetInfo],  # List may be empty if user has no tweets
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., user does not exist
            }

        Constraints:
            - User must exist in the platform.
            - All tweets returned have their user_id equal to the input user_id.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        tweets = [
            tweet_info for tweet_info in self.tweets.values()
            if tweet_info["user_id"] == user_id
        ]

        return { "success": True, "data": tweets }

    def get_tweet_sentiment(self, tweet_id: str) -> dict:
        """
        Retrieve the sentiment score for a tweet given its ID.

        Args:
            tweet_id (str): Unique identifier of the tweet.

        Returns:
            dict:
                - success: True and the sentiment_score (float) if found.
                - success: False and error message if tweet_id is not found.

        Constraints:
            - Tweet must exist in the system.
        """
        tweet = self.tweets.get(tweet_id)
        if not tweet:
            return { "success": False, "error": "Tweet not found" }
        return { "success": True, "data": tweet["sentiment_score"] }

    def get_tweet_engagement_metrics(self, tweet_id: str) -> dict:
        """
        Retrieve the engagement metrics (favorite_count, retweet_count, reply_count) for a tweet by id.

        Args:
            tweet_id (str): The unique identifier of the tweet.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": {
                            "tweet_id": str,
                            "favorite_count": int,
                            "retweet_count": int,
                            "reply_count": int
                        }
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # e.g., "Tweet not found"
                    }

        Constraints:
            - tweet_id must refer to an existing tweet in the platform.
        """
        tweet = self.tweets.get(tweet_id)
        if tweet is None:
            return {"success": False, "error": "Tweet not found"}

        result = {
            "tweet_id": tweet_id,
            "favorite_count": tweet["favorite_count"],
            "retweet_count": tweet["retweet_count"],
            "reply_count": tweet["reply_count"],
        }
        return {"success": True, "data": result}


    def update_tweet_content(
        self,
        tweet_id: str,
        new_text: Optional[str] = None,
        new_hashtags: Optional[List[str]] = None
    ) -> dict:
        """
        Modify the text and/or hashtags of a tweet and recalculate the sentiment score.

        Args:
            tweet_id (str): ID of the tweet to update.
            new_text (Optional[str]): New tweet text (if updating).
            new_hashtags (Optional[List[str]]): New list of hashtags (if updating).

        Returns:
            dict: On success,
                {
                    "success": True,
                    "message": <description>
                }
                On failure,
                {
                    "success": False,
                    "error": <error reason>
                }
        Constraints:
            - Tweet must exist.
            - At least one of new_text or new_hashtags must be provided.
            - Sentiment score must be recalculated when content is changed.
            - Engagement metrics are not altered.
        """
        tweet = self.tweets.get(tweet_id)
        if not tweet:
            return {"success": False, "error": f"Tweet with id {tweet_id} does not exist."}
    
        if new_text is None and new_hashtags is None:
            return {"success": False, "error": "No new_text or new_hashtags provided. Nothing to update."}
    
        updated = []
        if new_text is not None:
            tweet["text"] = new_text
            updated.append("text")
        if new_hashtags is not None:
            if not isinstance(new_hashtags, list) or not all(isinstance(ht, str) for ht in new_hashtags):
                return {"success": False, "error": "new_hashtags must be a list of strings."}
            tweet["hashtags"] = new_hashtags
            updated.append("hashtags")
    
        # Simulate sentiment score recalculation (stub implementation)
        def recalculate_sentiment(text: str) -> float:
            # Placeholder: e.g., positive if contains :)
            if not text:
                return 0.0
            return 1.0 if ":)" in text else -1.0 if ":(" in text else 0.0
    
        tweet["sentiment_score"] = recalculate_sentiment(tweet["text"])
    
        # Update timestamp to now
        tweet["timestamp"] = str(int(time.time()))
    
        return {
            "success": True,
            "message": f"Tweet {tweet_id} updated: {', '.join(updated)}; sentiment recalculated."
        }

    def update_sentiment_for_tweet(self, tweet_id: str) -> dict:
        """
        Recalculate and update the sentiment score for the specified tweet.
        (Uses a mock sentiment analysis function for demo purposes.)

        Args:
            tweet_id (str): The tweet's unique identifier.

        Returns:
            dict: 
                On success: { "success": True, "message": "Sentiment score updated for tweet <tweet_id>." }
                On failure: { "success": False, "error": "Tweet not found." }

        Constraints:
            - The specified tweet must exist.
            - Sentiment score must be a float (mocked for demo; replace with real analysis as needed).
        """
        if tweet_id not in self.tweets:
            return { "success": False, "error": "Tweet not found." }

        tweet = self.tweets[tweet_id]

        # Mock sentiment analysis: for demo, return +1.0 if text contains "good", -1.0 if "bad", 0 otherwise.
        text = tweet["text"].lower()
        if "good" in text:
            new_score = 1.0
        elif "bad" in text:
            new_score = -1.0
        else:
            new_score = 0.0

        tweet["sentiment_score"] = new_score
        self.tweets[tweet_id] = tweet  # (Likely unnecessary since dict is mutable, but explicit)

        return { "success": True, "message": f"Sentiment score updated for tweet {tweet_id}." }

    def update_user_profile(
        self,
        user_id: str,
        username: str = None,
        display_name: str = None,
        profile_image_url: str = None,
        follower_count: int = None,
        following_count: int = None,
        verified_status: bool = None
    ) -> dict:
        """
        Update user profile details to match a given set of provided parameters.

        Args:
            user_id (str): The ID of the user to update.
            username (str, optional): New username.
            display_name (str, optional): New display name.
            profile_image_url (str, optional): New profile image URL.
            follower_count (int, optional): New follower count (must be >= 0).
            following_count (int, optional): New following count (must be >= 0).
            verified_status (bool, optional): New verified status.

        Returns:
            dict: {
                "success": True,
                "message": "User profile updated successfully."
            }
            or
            {
                "success": False,
                "error": <error_reason>
            }

        Constraints:
            - User with user_id must exist.
            - Numeric counts must be non-negative integers if provided.
            - verified_status must be boolean if provided.
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found." }

        # Validate and update fields
        if username is not None:
            user["username"] = username
        if display_name is not None:
            user["display_name"] = display_name
        if profile_image_url is not None:
            user["profile_image_url"] = profile_image_url
        if follower_count is not None:
            if not isinstance(follower_count, int) or follower_count < 0:
                return { "success": False, "error": "Invalid follower_count value." }
            user["follower_count"] = follower_count
        if following_count is not None:
            if not isinstance(following_count, int) or following_count < 0:
                return { "success": False, "error": "Invalid following_count value." }
            user["following_count"] = following_count
        if verified_status is not None:
            if not isinstance(verified_status, bool):
                return { "success": False, "error": "Invalid verified_status value." }
            user["verified_status"] = verified_status

        return { "success": True, "message": "User profile updated successfully." }

    def update_tweet_engagement_metrics(
        self,
        tweet_id: str,
        favorite_count: int = None,
        retweet_count: int = None,
        reply_count: int = None
    ) -> dict:
        """
        Update engagement metrics of a tweet (favorite_count, retweet_count, reply_count).

        Args:
            tweet_id (str): The ID of the tweet to update.
            favorite_count (int, optional): New favorite count (must be non-negative).
            retweet_count (int, optional): New retweet count (must be non-negative).
            reply_count (int, optional): New reply count (must be non-negative).

        Returns:
            dict: {
                "success": True,
                "message": "Tweet engagement metrics updated"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Tweet must exist.
            - Updated counts must be non-negative integers if provided.
            - At least one count must be supplied.
        """

        if tweet_id not in self.tweets:
            return { "success": False, "error": "Tweet does not exist" }

        if favorite_count is None and retweet_count is None and reply_count is None:
            return { "success": False, "error": "No engagement metrics provided to update" }

        if (
            (favorite_count is not None and (not isinstance(favorite_count, int) or favorite_count < 0)) or
            (retweet_count is not None and (not isinstance(retweet_count, int) or retweet_count < 0)) or
            (reply_count is not None and (not isinstance(reply_count, int) or reply_count < 0))
        ):
            return { "success": False, "error": "Engagement metrics must be non-negative integers" }

        tweet = self.tweets[tweet_id]
        if favorite_count is not None:
            tweet["favorite_count"] = favorite_count
        if retweet_count is not None:
            tweet["retweet_count"] = retweet_count
        if reply_count is not None:
            tweet["reply_count"] = reply_count

        return { "success": True, "message": "Tweet engagement metrics updated" }

    def add_new_tweet(
        self,
        tweet_id: str,
        user_id: str,
        text: str,
        timestamp: str,
        sentiment_score: float,
        favorite_count: int,
        retweet_count: int,
        reply_count: int,
        hashtags: list,
        language: str
    ) -> dict:
        """
        Insert a new tweet into the platform, with user association and initial engagement metrics.

        Args:
            tweet_id (str): Unique identifier for the tweet.
            user_id (str): User identifier (must exist in platform).
            text (str): Content of the tweet.
            timestamp (str): When the tweet was posted.
            sentiment_score (float): Initial sentiment analysis score.
            favorite_count (int): Initial favorite count (must be >= 0).
            retweet_count (int): Initial retweet count (must be >= 0).
            reply_count (int): Initial reply count (must be >= 0).
            hashtags (List[str]): List of hashtags.
            language (str): Tweet language (e.g., 'en').

        Returns:
            dict (success/error message)
    
        Constraints:
            - tweet_id must be unique.
            - user_id must exist in self.users.
            - favorite_count, retweet_count, reply_count must be non-negative integers.
            - sentiment_score must be a float.
        """
        # Check for existing tweet_id
        if tweet_id in self.tweets:
            return { "success": False, "error": "Tweet ID already exists" }

        # Check user existence
        if user_id not in self.users:
            return { "success": False, "error": "Associated user does not exist" }

        # Engagement metric validation
        err_msg = "Engagement metrics must be non-negative integers"
        if not (isinstance(favorite_count, int) and favorite_count >= 0):
            return { "success": False, "error": err_msg }
        if not (isinstance(retweet_count, int) and retweet_count >= 0):
            return { "success": False, "error": err_msg }
        if not (isinstance(reply_count, int) and reply_count >= 0):
            return { "success": False, "error": err_msg }

        # Sentiment score
        if not isinstance(sentiment_score, float):
            return { "success": False, "error": "Sentiment score must be a float" }

        # hashtags must be a list of strings
        if not (isinstance(hashtags, list) and all(isinstance(ht, str) for ht in hashtags)):
            return { "success": False, "error": "Hashtags must be provided as a list of strings" }

        # Create and insert
        self.tweets[tweet_id] = {
            "tweet_id": tweet_id,
            "user_id": user_id,
            "text": text,
            "timestamp": timestamp,
            "sentiment_score": sentiment_score,
            "favorite_count": favorite_count,
            "retweet_count": retweet_count,
            "reply_count": reply_count,
            "hashtags": hashtags,
            "language": language
        }
        return { "success": True, "message": "New tweet added." }

    def add_new_user(
        self,
        user_id: str,
        username: str,
        display_name: str,
        profile_image_url: str,
        follower_count: int,
        following_count: int,
        verified_status: bool
    ) -> dict:
        """
        Insert a new user profile into the platform.

        Args:
            user_id (str): Unique identifier for the user.
            username (str): Twitter handle/username.
            display_name (str): Display name of the user.
            profile_image_url (str): URL to the profile image.
            follower_count (int): Number of followers (must be >= 0).
            following_count (int): Number of accounts the user is following (must be >= 0).
            verified_status (bool): Whether the user is verified.

        Returns:
            dict: {
                "success": True,
                "message": "User profile added successfully."
            }
            or
            {
                "success": False,
                "error": "Reason for failure."
            }

        Constraints:
            - user_id must be unique.
            - follower_count and following_count must be non-negative integers.
            - All attributes required; types should match specification.
        """

        if user_id in self.users:
            return { "success": False, "error": "User ID already exists." }
        if not isinstance(user_id, str) or not user_id:
            return { "success": False, "error": "Invalid or missing user_id." }
        if not isinstance(username, str) or not username:
            return { "success": False, "error": "Invalid or missing username." }
        if not isinstance(display_name, str) or not display_name:
            return { "success": False, "error": "Invalid or missing display_name." }
        if not isinstance(profile_image_url, str) or not profile_image_url:
            return { "success": False, "error": "Invalid or missing profile_image_url." }
        if not isinstance(follower_count, int) or follower_count < 0:
            return { "success": False, "error": "Invalid follower_count (must be non-negative integer)." }
        if not isinstance(following_count, int) or following_count < 0:
            return { "success": False, "error": "Invalid following_count (must be non-negative integer)." }
        if not isinstance(verified_status, bool):
            return { "success": False, "error": "Invalid verified_status (must be boolean)." }

        user_info: UserInfo = {
            "user_id": user_id,
            "username": username,
            "display_name": display_name,
            "profile_image_url": profile_image_url,
            "follower_count": follower_count,
            "following_count": following_count,
            "verified_status": verified_status
        }
        self.users[user_id] = user_info
        return { "success": True, "message": "User profile added successfully." }

    def delete_tweet(self, tweet_id: str) -> dict:
        """
        Remove a tweet from the database by its unique tweet_id.

        Args:
            tweet_id (str): The unique identifier of the tweet to delete.

        Returns:
            dict:
                - On success: { "success": True, "message": "Tweet <tweet_id> deleted successfully." }
                - On failure: { "success": False, "error": "reason" }

        Constraints:
            - The tweet must exist in the database.
            - Does not affect user records.
        """
        if tweet_id not in self.tweets:
            return { "success": False, "error": f"Tweet {tweet_id} does not exist." }
    
        del self.tweets[tweet_id]
        return { "success": True, "message": f"Tweet {tweet_id} deleted successfully." }

    def delete_user(self, user_id: str) -> dict:
        """
        Remove a user profile and all their associated tweets from the platform.

        Args:
            user_id (str): ID of the user to be deleted.

        Returns:
            dict: {
                "success": True,
                "message": str  # Description, includes number of tweets deleted
            }
            or
            {
                "success": False,
                "error": str  # Error message, e.g. user does not exist
            }

        Constraints:
            - User must exist.
            - All tweets associated with the user must also be deleted to maintain referential integrity.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        # Delete user's tweets
        tweets_to_delete = [tweet_id for tweet_id, tweet in self.tweets.items() if tweet["user_id"] == user_id]
        for tweet_id in tweets_to_delete:
            del self.tweets[tweet_id]

        # Delete user profile
        del self.users[user_id]

        return {
            "success": True,
            "message": f"User '{user_id}' deleted. {len(tweets_to_delete)} tweets removed."
        }


class TwitterAnalyticsPlatform(BaseEnv):
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

    def search_tweets_by_keyword(self, **kwargs):
        return self._call_inner_tool('search_tweets_by_keyword', kwargs)

    def search_tweets_by_hashtag(self, **kwargs):
        return self._call_inner_tool('search_tweets_by_hashtag', kwargs)

    def filter_tweets_by_engagement(self, **kwargs):
        return self._call_inner_tool('filter_tweets_by_engagement', kwargs)

    def sort_tweets_by_favorite_count(self, **kwargs):
        return self._call_inner_tool('sort_tweets_by_favorite_count', kwargs)

    def get_user_info_by_tweet(self, **kwargs):
        return self._call_inner_tool('get_user_info_by_tweet', kwargs)

    def get_user_info_by_user_id(self, **kwargs):
        return self._call_inner_tool('get_user_info_by_user_id', kwargs)

    def get_tweet_by_id(self, **kwargs):
        return self._call_inner_tool('get_tweet_by_id', kwargs)

    def get_tweets_by_user_id(self, **kwargs):
        return self._call_inner_tool('get_tweets_by_user_id', kwargs)

    def get_tweet_sentiment(self, **kwargs):
        return self._call_inner_tool('get_tweet_sentiment', kwargs)

    def get_tweet_engagement_metrics(self, **kwargs):
        return self._call_inner_tool('get_tweet_engagement_metrics', kwargs)

    def update_tweet_content(self, **kwargs):
        return self._call_inner_tool('update_tweet_content', kwargs)

    def update_sentiment_for_tweet(self, **kwargs):
        return self._call_inner_tool('update_sentiment_for_tweet', kwargs)

    def update_user_profile(self, **kwargs):
        return self._call_inner_tool('update_user_profile', kwargs)

    def update_tweet_engagement_metrics(self, **kwargs):
        return self._call_inner_tool('update_tweet_engagement_metrics', kwargs)

    def add_new_tweet(self, **kwargs):
        return self._call_inner_tool('add_new_tweet', kwargs)

    def add_new_user(self, **kwargs):
        return self._call_inner_tool('add_new_user', kwargs)

    def delete_tweet(self, **kwargs):
        return self._call_inner_tool('delete_tweet', kwargs)

    def delete_user(self, **kwargs):
        return self._call_inner_tool('delete_user', kwargs)

