# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
from datetime import datetime



class RestaurantInfo(TypedDict):
    restaurant_id: str
    name: str
    address: str
    cuisine_type: str
    average_rating: float
    status: str

class ReviewInfo(TypedDict):
    review_id: str
    restaurant_id: str
    user_id: str
    rating: int
    comment: str
    timestamp: str  # could also be float, depending on time representation

class UserInfo(TypedDict):
    user_id: str
    user_name: str
    account_status: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for managing restaurant reviews.
        """

        # Restaurants: {restaurant_id: RestaurantInfo}
        # Entity: Restaurant (restaurant_id, name, address, cuisine_type, average_rating, status)
        self.restaurants: Dict[str, RestaurantInfo] = {}

        # Reviews: {review_id: ReviewInfo}
        # Entity: Review (review_id, restaurant_id, user_id, rating, comment, timestamp)
        self.reviews: Dict[str, ReviewInfo] = {}

        # Users: {user_id: UserInfo}
        # Entity: User (user_id, user_name, account_status)
        self.users: Dict[str, UserInfo] = {}

        # Constraints (to be enforced in logic, listed for reference):
        # - Each review must be associated with a valid restaurant_id.
        # - Ratings must fall within an allowed range (e.g., 1–5 stars).
        # - Each review must have a timestamp.
        # - Only users with a valid account_status can submit reviews.

    def get_restaurant_by_id(self, restaurant_id: str) -> dict:
        """
        Retrieve all information about a restaurant by its unique restaurant_id.

        Args:
            restaurant_id (str): The unique identifier for the restaurant.

        Returns:
            dict: {
                "success": True,
                "data": RestaurantInfo
            }
            or
            {
                "success": False,
                "error": "Restaurant not found"
            }

        Constraints:
            - The provided restaurant_id must exist in the system.
        """
        if restaurant_id not in self.restaurants:
            return { "success": False, "error": "Restaurant not found" }
        restaurant_info = self.restaurants[restaurant_id]
        return { "success": True, "data": restaurant_info }

    def list_all_restaurants(self) -> dict:
        """
        List all restaurants registered in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[RestaurantInfo],  # List of all registered restaurants (may be empty)
            }
        Constraints:
            - None.
            - Returns empty list if no restaurants exist.
        """
        all_restaurants = list(self.restaurants.values())
        return {
            "success": True,
            "data": all_restaurants
        }

    def search_restaurants_by_name(self, query: str) -> dict:
        """
        Search for restaurants by partial or full name match (case-insensitive).

        Args:
            query (str): The substring (or full string) to match against restaurant names.

        Returns:
            dict: {
                "success": True,
                "data": list of RestaurantInfo dicts matching the query (may be empty)
            }
            or
            {
                "success": False,
                "error": str, // Input error
            }

        Constraints:
            - Query must be a non-empty string.
            - Match is case-insensitive substring.
        """
        if not isinstance(query, str) or not query.strip():
            return { "success": False, "error": "Search query must be a non-empty string." }

        lowered_query = query.lower()
        results = [
            restaurant for restaurant in self.restaurants.values()
            if lowered_query in restaurant["name"].lower()
        ]

        return { "success": True, "data": results }

    def get_reviews_by_restaurant_id(self, restaurant_id: str) -> dict:
        """
        Retrieve all reviews for a restaurant with a given restaurant_id.

        Args:
            restaurant_id (str): The unique identifier of the target restaurant.

        Returns:
            dict:
                - If the restaurant exists:
                    {
                        "success": True,
                        "data": List[ReviewInfo]  # All reviews for this restaurant (empty list if none)
                    }
                - If the restaurant_id does not exist:
                    {
                        "success": False,
                        "error": "Restaurant not found"
                    }

        Constraints:
            - The given restaurant_id must exist.
        """
        if restaurant_id not in self.restaurants:
            return { "success": False, "error": "Restaurant not found" }

        review_list = [
            review for review in self.reviews.values()
            if review["restaurant_id"] == restaurant_id
        ]
        return { "success": True, "data": review_list }

    def get_recent_reviews_by_restaurant_id(
        self, 
        restaurant_id: str, 
        limit: int = None, 
        since: str = None
    ) -> dict:
        """
        Retrieve the most recent reviews for a given restaurant.
    
        Args:
            restaurant_id (str): The ID of the restaurant whose reviews to fetch.
            limit (int, optional): Maximum number of recent reviews to return (most recent first). If None, return all.
            since (str, optional): Only include reviews AFTER this timestamp. Format should match ReviewInfo["timestamp"].
    
        Returns:
            dict: {
                "success": True,
                "data": List[ReviewInfo]  # Most recent reviews (may be empty)
            }
            or
            {
                "success": False,
                "error": str
            }
        Constraints:
            - Only reviews associated with a valid restaurant_id are considered.
            - Reviews returned are sorted with most recent first.
            - Optional filter by "since" timestamp.
            - Optional limit on number of reviews returned.
        """
        # Check restaurant exists
        if restaurant_id not in self.restaurants:
            return { "success": False, "error": "Restaurant does not exist" }
    
        # Select reviews for this restaurant
        reviews = [
            review for review in self.reviews.values()
            if review["restaurant_id"] == restaurant_id
        ]

        # Filter by 'since' timestamp if provided
        if since is not None:
            # Assume lexicographical comparison is valid (e.g. ISO 8601 strings)
            reviews = [r for r in reviews if r["timestamp"] > since]
    
        # Sort by timestamp descending (most recent first)
        reviews.sort(key=lambda r: r["timestamp"], reverse=True)
    
        # Apply limit if provided and valid
        if limit is not None:
            try:
                limit_val = int(limit)
                if limit_val > 0:
                    reviews = reviews[:limit_val]
            except (TypeError, ValueError):
                # Ignore invalid limit, return all
                pass
    
        return { "success": True, "data": reviews }

    def get_review_by_id(self, review_id: str) -> dict:
        """
        Retrieve a review's information by its unique review_id.

        Args:
            review_id (str): Unique identifier of the review.

        Returns:
            dict: 
              - If found: {"success": True, "data": ReviewInfo}
              - If not found: {"success": False, "error": "Review not found"}
        """
        if not review_id or review_id not in self.reviews:
            return {"success": False, "error": "Review not found"}
        return {"success": True, "data": self.reviews[review_id]}

    def list_reviews_by_user_id(self, user_id: str) -> dict:
        """
        Show all reviews submitted by a specific user.

        Args:
            user_id (str): The identifier of the user whose reviews should be retrieved.

        Returns:
            dict:
              - success: True and data: list of ReviewInfo submitted by this user (may be an empty list)
              - success: False and error: error message if user does not exist

        Constraints:
            - The specified user_id must exist in the Users table.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        user_reviews = [
            review_info for review_info in self.reviews.values()
            if review_info['user_id'] == user_id
        ]
        return { "success": True, "data": user_reviews }

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user information by user_id.

        Args:
            user_id (str): Unique identifier for the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo  # if user found
            }
            or
            {
                "success": False,
                "error": str  # error message if user not found
            }
        """
        user_info = self.users.get(user_id)
        if user_info is None:
            return {
                "success": False,
                "error": f"User with user_id '{user_id}' does not exist."
            }
        return {
            "success": True,
            "data": user_info
        }

    def get_user_by_name(self, user_name: str) -> dict:
        """
        Retrieve user information (UserInfo) by user_name.

        Args:
            user_name (str): The user name to look up.

        Returns:
            dict:
                - On success: { "success": True, "data": UserInfo }
                - On error (not found): { "success": False, "error": "User not found" }

        Constraints:
            - Assumes user_name is unique in the system.
        """
        for user in self.users.values():
            if user["user_name"] == user_name:
                return { "success": True, "data": user }
        return { "success": False, "error": "User not found" }

    def check_user_account_status(self, user_id: str) -> dict:
        """
        Retrieve the account_status of the specified user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict:
                On success:
                    {
                      "success": True,
                      "data": str,  # The user's account status
                    }
                On failure:
                    {
                      "success": False,
                      "error": str  # Description of the error (e.g., user does not exist)
                    }

        Constraints:
            - The specified user_id must exist in the environment.
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User does not exist" }
        return { "success": True, "data": user["account_status"] }

    def add_review(
        self,
        review_id: str,
        restaurant_id: str,
        user_id: str,
        rating: int,
        comment: str,
        timestamp: str
    ) -> dict:
        """
        Submit a new review for a restaurant.

        Args:
            review_id (str): Unique identifier for the review (must be new).
            restaurant_id (str): Restaurant being reviewed (must exist).
            user_id (str): Authoring user (must exist and account_status valid).
            rating (int): Review rating (must be 1–5 inclusive).
            comment (str): Review text/comment.
            timestamp (str): Timestamp of submission (must be provided).

        Returns:
            dict:
                - { "success": True, "message": "Review added successfully." }
                - { "success": False, "error": "<reason>" }

        Constraints:
            - Each review must have a unique review_id.
            - restaurant_id must be valid.
            - user_id must be valid and have an account_status of "active".
            - rating must be in [1, 5].
            - timestamp must be provided (not empty).
        """
        # Check review_id uniqueness
        if review_id in self.reviews:
            return {"success": False, "error": "Review ID already exists."}

        # Validate restaurant_id
        if restaurant_id not in self.restaurants:
            return {"success": False, "error": "Invalid restaurant_id; restaurant not found."}

        # Validate user_id & account_status
        user_info = self.users.get(user_id)
        if not user_info:
            return {"success": False, "error": "Invalid user_id; user not found."}
        if user_info.get("account_status", "").lower() != "active":
            return {"success": False, "error": "User account is not active."}

        # Validate rating
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            return {"success": False, "error": "Rating must be an integer between 1 and 5."}

        # Validate timestamp
        if not timestamp or not str(timestamp).strip():
            return {"success": False, "error": "Timestamp must be provided."}

        # Add the review
        new_review: ReviewInfo = {
            "review_id": review_id,
            "restaurant_id": restaurant_id,
            "user_id": user_id,
            "rating": rating,
            "comment": comment,
            "timestamp": timestamp
        }
        self.reviews[review_id] = new_review

        return {"success": True, "message": "Review added successfully."}

    def edit_review(
        self,
        review_id: str,
        user_id: str,
        rating: int = None,
        comment: str = None,
        timestamp: str = None,
    ) -> dict:
        """
        Modify the content and/or rating of an existing review.
        Only the review's owner or an admin can perform the modification.

        Args:
            review_id (str): ID of the review to edit.
            user_id (str): ID of the user attempting the edit.
            rating (int, optional): New rating value (must be in allowed range, if provided).
            comment (str, optional): New comment text (if provided).
            timestamp (str, optional): Updated timestamp (must be provided to ensure review freshness).

        Returns:
            dict: {
                "success": True,
                "message": "Review updated successfully."
            }
            OR
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Only the review owner or users with account_status "admin" can edit the review.
            - If rating is provided, must be between 1 and 5 inclusive.
            - At least one of rating or comment must be provided.
            - Review and user must exist.
            - Review must have an updated timestamp.
        """
        # Check review existence
        review_info = self.reviews.get(review_id)
        if not review_info:
            return {"success": False, "error": "Review does not exist."}

        # Check user existence
        user_info = self.users.get(user_id)
        if not user_info:
            return {"success": False, "error": "User does not exist."}

        # Permission check: user must be owner or admin
        is_owner = (review_info["user_id"] == user_id)
        is_admin = (user_info.get("account_status", "").lower() == "admin")
        if not (is_owner or is_admin):
            return {"success": False, "error": "Permission denied: not owner or admin."}

        # At least one editable field should be provided
        if rating is None and comment is None:
            return {"success": False, "error": "No new rating or comment provided for edit."}

        # Validate and update fields
        if rating is not None:
            if not isinstance(rating, int) or not (1 <= rating <= 5):
                return {"success": False, "error": "Rating must be an integer between 1 and 5."}
            review_info["rating"] = rating

        if comment is not None:
            review_info["comment"] = comment

        # Timestamp update required to reflect change (must have one!)
        review_info["timestamp"] = timestamp if timestamp is not None else datetime.utcnow().isoformat()

        # Write back to storage
        self.reviews[review_id] = review_info

        # After rating update, recalc average rating for restaurant
        restaurant_id = review_info["restaurant_id"]
        self.update_restaurant_average_rating(restaurant_id)

        return {"success": True, "message": "Review updated successfully."}

    def delete_review(self, review_id: str, requesting_user_id: str) -> dict:
        """
        Remove a review from the system. Only the review's owner or an admin can delete a review.

        Args:
            review_id (str): The ID of the review to delete.
            requesting_user_id (str): The ID of the user attempting the deletion.

        Returns:
            dict: 
            - { "success": True, "message": "Review deleted." }
            - { "success": False, "error": str }
    
        Constraints:
            - The review must exist.
            - The requesting user must exist.
            - Only the owner or an admin can perform the deletion.
        """
        # Check if review exists
        review = self.reviews.get(review_id)
        if review is None:
            return { "success": False, "error": "Review does not exist." }
    
        # Check if requesting user exists
        user = self.users.get(requesting_user_id)
        if user is None:
            return { "success": False, "error": "Requesting user does not exist." }

        # Check authorization
        is_owner = review["user_id"] == requesting_user_id
        is_admin = user.get("account_status", "").lower() == "admin"
        if not (is_owner or is_admin):
            return { "success": False, "error": "Permission denied: must be owner or admin to delete review." }

        # Delete the review
        del self.reviews[review_id]
        return { "success": True, "message": "Review deleted." }

    def update_restaurant_average_rating(self, restaurant_id: str) -> dict:
        """
        Recompute and update a restaurant's average_rating based on current reviews.

        Args:
            restaurant_id (str): The unique identifier of the restaurant.

        Returns:
            dict: {
                "success": True,
                "message": str  # Description of operation on success
            }
            or
            {
                "success": False,
                "error": str  # Error message if restaurant not found
            }

        Constraints:
            - Restaurant must exist.
            - Only uses reviews that currently exist for the specified restaurant.
            - If no reviews exist for the restaurant, average_rating is set to 0.0.
        """
        if restaurant_id not in self.restaurants:
            return { "success": False, "error": "Restaurant not found" }

        # Gather ratings for this restaurant
        ratings = [
            review["rating"] for review in self.reviews.values()
            if review["restaurant_id"] == restaurant_id
        ]

        if ratings:
            avg = sum(ratings) / len(ratings)
        else:
            avg = 0.0

        self.restaurants[restaurant_id]["average_rating"] = float(avg)

        return {
            "success": True,
            "message": f"Average rating updated for restaurant {restaurant_id}."
        }

    def update_restaurant_info(
        self, 
        restaurant_id: str, 
        name: str = None, 
        address: str = None, 
        cuisine_type: str = None, 
        status: str = None
    ) -> dict:
        """
        Modify a restaurant's descriptive information.

        Args:
            restaurant_id (str): The unique identifier of the restaurant to update.
            name (str, optional): New name for the restaurant.
            address (str, optional): New address for the restaurant.
            cuisine_type (str, optional): New cuisine type.
            status (str, optional): New status for the restaurant.

        Returns:
            dict: 
                On success: { "success": True, "message": "Restaurant info updated" }
                On failure: { "success": False, "error": str }

        Constraints:
            - restaurant_id must refer to an existing restaurant.
            - Only name, address, cuisine_type, and status are updatable.
            - If no valid fields are provided, no update is performed and an error is returned.
        """
        if restaurant_id not in self.restaurants:
            return { "success": False, "error": "Restaurant does not exist" }
    
        restaurant = self.restaurants[restaurant_id]
        updated = False

        if name is not None:
            restaurant["name"] = name
            updated = True
        if address is not None:
            restaurant["address"] = address
            updated = True
        if cuisine_type is not None:
            restaurant["cuisine_type"] = cuisine_type
            updated = True
        if status is not None:
            restaurant["status"] = status
            updated = True

        if not updated:
            return { "success": False, "error": "No updatable fields provided" }

        self.restaurants[restaurant_id] = restaurant
        return { "success": True, "message": "Restaurant info updated" }

    def update_user_account_status(self, user_id: str, new_status: str) -> dict:
        """
        Change a user's account status (e.g., activate or suspend account).

        Args:
            user_id (str): The unique identifier of the user.
            new_status (str): The new account status to set (e.g., "active", "suspended").

        Returns:
            dict: {
                "success": True,
                "message": "User account status updated."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - User must exist in the system.
            - new_status must be among allowed status values.
        """
        # Define allowed account statuses; could be expanded per business logic
        allowed_statuses = {"active", "suspended"}

        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User not found."}

        if new_status not in allowed_statuses:
            return {"success": False, "error": f"Invalid account status '{new_status}'."}

        user["account_status"] = new_status
        return {"success": True, "message": "User account status updated."}

    def bulk_delete_reviews_by_user(self, user_id: str) -> dict:
        """
        Remove all reviews submitted by a specific user.

        Args:
            user_id (str): The ID of the user whose reviews will be deleted.

        Returns:
            dict: {
                "success": True,
                "message": str  # Success message with number of reviews deleted
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (e.g., user not found)
            }

        Constraints:
            - User must exist.
            - All reviews authored by the user are deleted.
            - Does not update restaurant average ratings.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        # Find all review_ids for this user
        reviews_to_delete = [
            review_id for review_id, review_info in self.reviews.items()
            if review_info["user_id"] == user_id
        ]
        num_deleted = len(reviews_to_delete)

        for review_id in reviews_to_delete:
            del self.reviews[review_id]

        return {
            "success": True,
            "message": f"Removed {num_deleted} reviews by user {user_id}"
        }


class RestaurantReviewManagementSystem(BaseEnv):
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
            if key == "update_restaurant_average_rating":
                setattr(env, "_update_restaurant_average_rating_state", copy.deepcopy(value))
                continue
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

    def get_restaurant_by_id(self, **kwargs):
        return self._call_inner_tool('get_restaurant_by_id', kwargs)

    def list_all_restaurants(self, **kwargs):
        return self._call_inner_tool('list_all_restaurants', kwargs)

    def search_restaurants_by_name(self, **kwargs):
        return self._call_inner_tool('search_restaurants_by_name', kwargs)

    def get_reviews_by_restaurant_id(self, **kwargs):
        return self._call_inner_tool('get_reviews_by_restaurant_id', kwargs)

    def get_recent_reviews_by_restaurant_id(self, **kwargs):
        return self._call_inner_tool('get_recent_reviews_by_restaurant_id', kwargs)

    def get_review_by_id(self, **kwargs):
        return self._call_inner_tool('get_review_by_id', kwargs)

    def list_reviews_by_user_id(self, **kwargs):
        return self._call_inner_tool('list_reviews_by_user_id', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def get_user_by_name(self, **kwargs):
        return self._call_inner_tool('get_user_by_name', kwargs)

    def check_user_account_status(self, **kwargs):
        return self._call_inner_tool('check_user_account_status', kwargs)

    def add_review(self, **kwargs):
        return self._call_inner_tool('add_review', kwargs)

    def edit_review(self, **kwargs):
        return self._call_inner_tool('edit_review', kwargs)

    def delete_review(self, **kwargs):
        return self._call_inner_tool('delete_review', kwargs)

    def update_restaurant_average_rating(self, **kwargs):
        return self._call_inner_tool('update_restaurant_average_rating', kwargs)

    def update_restaurant_info(self, **kwargs):
        return self._call_inner_tool('update_restaurant_info', kwargs)

    def update_user_account_status(self, **kwargs):
        return self._call_inner_tool('update_user_account_status', kwargs)

    def bulk_delete_reviews_by_user(self, **kwargs):
        return self._call_inner_tool('bulk_delete_reviews_by_user', kwargs)
