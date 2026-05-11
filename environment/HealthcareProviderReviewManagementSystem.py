# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict, Tuple

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict



class ProviderInfo(TypedDict):
    provider_id: str
    name: str
    specialty: str
    location: str
    profile_details: str
    aggregate_rating: float
    review_count: int

class ReviewInfo(TypedDict):
    review_id: str
    provider_id: str
    user_id: str
    rating: float
    review_text: str
    submission_date: str
    status: str

class UserInfo(TypedDict):
    user_id: str
    name: str
    account_status: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Providers: {provider_id: ProviderInfo}
        # entity: Provider (provider_id, name, specialty, location, profile_details, aggregate_rating, review_count)
        self.providers: Dict[str, ProviderInfo] = {}

        # Reviews: {review_id: ReviewInfo}
        # entity: Review (review_id, provider_id, user_id, rating, review_text, submission_date, status)
        self.reviews: Dict[str, ReviewInfo] = {}

        # Users: {user_id: UserInfo}
        # entity: User (user_id, name, account_status)
        self.users: Dict[str, UserInfo] = {}

        # Constraints (for future logic):
        # - A review must be linked to an existing provider and a registered user.
        # - The rating value must fall within an accepted range (e.g., 1.0 to 5.0).
        # - Aggregate ratings and review counts on the provider profile should update when reviews are added, edited, or removed.
        # - Duplicate reviews (from the same user on the same provider) may be restricted.
        # - Review text may be subject to moderation or character limits.

    @staticmethod
    def _is_counted_in_aggregate(status: str) -> bool:
        normalized = (status or "").strip().lower()
        return normalized in {"active", "published", "verified", "pending", "visible"}

    def _recompute_provider_aggregate(self, provider_id: str) -> Tuple[float, int]:
        relevant_reviews = [
            review
            for review in self.reviews.values()
            if review["provider_id"] == provider_id and self._is_counted_in_aggregate(review.get("status"))
        ]
        review_count = len(relevant_reviews)
        aggregate_rating = sum(review["rating"] for review in relevant_reviews) / review_count if review_count else 0.0
        if provider_id in self.providers:
            self.providers[provider_id]["aggregate_rating"] = aggregate_rating
            self.providers[provider_id]["review_count"] = review_count
        return aggregate_rating, review_count

    def get_provider_by_name(self, name: str) -> dict:
        """
        Retrieve a provider's profile information using their exact name.

        Args:
            name (str): The full name of the provider to look up.

        Returns:
            dict: 
                - On success:
                    {"success": True, "data": ProviderInfo (dict)}
                - On failure:
                    {"success": False, "error": "Provider not found"}

        Constraints:
            - Name lookup is exact and case-sensitive.
            - Returns the first match if multiple providers have the same name.
        """
        if not name or not isinstance(name, str):
            return {"success": False, "error": "Provider not found"}

        for provider in self.providers.values():
            if provider["name"] == name:
                return {"success": True, "data": provider}
        return {"success": False, "error": "Provider not found"}

    def get_provider_by_id(self, provider_id: str) -> dict:
        """
        Fetch provider details by provider_id.

        Args:
            provider_id (str): The unique identifier of the provider.

        Returns:
            dict:
                If found:
                    {
                        "success": True,
                        "data": ProviderInfo  # Details about the provider
                    }
                If not found:
                    {
                        "success": False,
                        "error": "Provider not found"
                    }

        Constraints:
            - The provider_id must exist in the system.
        """
        provider = self.providers.get(provider_id)
        if provider is None:
            return { "success": False, "error": "Provider not found" }
        return { "success": True, "data": provider }

    def list_all_providers(self) -> dict:
        """
        Return a list of all providers in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[ProviderInfo]  # All providers (could be empty)
            }
        """
        providers_list = list(self.providers.values())
        return { "success": True, "data": providers_list }

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Fetch a user's profile based on their user_id.

        Args:
            user_id (str): The unique identifier for the user.

        Returns:
            dict:
                - If successful:
                    {
                        "success": True,
                        "data": UserInfo  # The user's profile dictionary
                    }
                - If user not found:
                    {
                        "success": False,
                        "error": "User not found"
                    }

        Constraints:
            - The user_id must exist in the system.
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User not found" }

        return { "success": True, "data": user }

    def get_user_by_name(self, name: str) -> dict:
        """
        Retrieve user record(s) by their display name.

        Args:
            name (str): The display name to search for.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[UserInfo],  # all users with the matching name
                    }
                On failure:
                    {
                        "success": False,
                        "error": "No user found with the specified name."
                    }
        Notes:
            - Multiple users may share the same display name; all will be returned.
        """
        matches = [
            user
            for user in self.users.values()
            if user["name"] == name
        ]

        if not matches:
            return {"success": False, "error": "No user found with the specified name."}
        return {"success": True, "data": matches}

    def check_user_account_status(self, user_id: str) -> dict:
        """
        Check if a user is active and eligible to submit reviews.

        Args:
            user_id (str): The unique identifier of the user to check.

        Returns:
            dict:
              - On success: {
                    "success": True,
                    "data": {
                        "eligible": bool,         # True if user is eligible ("active"), otherwise False.
                        "account_status": str     # The current user account status
                    }
                }
              - On failure: {
                    "success": False,
                    "error": "User does not exist"
                }

        Constraints:
            - User must exist.
            - User is eligible if account_status == "active".
        """
        user_info = self.users.get(user_id)
        if not user_info:
            return {"success": False, "error": "User does not exist"}

        eligible = user_info.get("account_status", "").lower() == "active"
        return {
            "success": True,
            "data": {
                "eligible": eligible,
                "account_status": user_info.get("account_status", "")
            }
        }

    def list_reviews_for_provider(self, provider_id: str) -> dict:
        """
        List all reviews for a specific provider.

        Args:
            provider_id (str): The provider's unique ID.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[ReviewInfo]  # all reviews for this provider (may be empty)
                    }
                On error:
                    {
                        "success": False,
                        "error": str  # error message if provider not found
                    }

        Constraints:
            - provider_id must exist in providers.
        """
        if provider_id not in self.providers:
            return { "success": False, "error": "Provider does not exist" }

        reviews = [
            review for review in self.reviews.values()
            if review["provider_id"] == provider_id
        ]
        return { "success": True, "data": reviews }

    def list_reviews_by_user(self, user_id: str) -> dict:
        """
        List all reviews submitted by a specific user.

        Args:
            user_id (str): The unique ID of the user.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": List[ReviewInfo],  # List of reviews by the user (may be empty)
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # e.g., "User does not exist"
                    }

        Constraints:
            - user_id must exist in the system.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        result = [
            review for review in self.reviews.values()
            if review["user_id"] == user_id
        ]
        return { "success": True, "data": result }

    def get_review_by_id(self, review_id: str) -> dict:
        """
        Retrieve the full details of a review via review_id.

        Args:
            review_id (str): The unique identifier for the review.

        Returns:
            dict: 
                - On success: {"success": True, "data": ReviewInfo}
                - On failure (not found): {"success": False, "error": "Review not found"}
        Constraints:
            - The review_id must exist in the system.
        """
        review = self.reviews.get(review_id)
        if not review:
            return { "success": False, "error": "Review not found" }
        return { "success": True, "data": review }

    def check_duplicate_review(self, user_id: str, provider_id: str) -> dict:
        """
        Verify whether the specified user has already submitted a review for the given provider.

        Args:
            user_id (str): The ID of the user to check.
            provider_id (str): The ID of the provider to check.

        Returns:
            dict: 
                If user or provider does not exist:
                    { "success": False, "error": <reason> }
                On success:
                    { "success": True, "data": bool }
                    # data=True if duplicate exists; False otherwise.

        Constraints:
            - User must exist.
            - Provider must exist.
            - A review is duplicate if any review exists in self.reviews where
              review['user_id'] == user_id and review['provider_id'] == provider_id
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
        if provider_id not in self.providers:
            return { "success": False, "error": "Provider does not exist" }

        for review in self.reviews.values():
            if review["user_id"] == user_id and review["provider_id"] == provider_id:
                return { "success": True, "data": True }

        return { "success": True, "data": False }

    def get_provider_aggregate_rating(self, provider_id: str) -> dict:
        """
        Query the current aggregate rating and review count for a provider.

        Args:
            provider_id (str): The unique identifier for the provider.

        Returns:
            dict: 
                On success:
                    {
                      "success": True,
                      "data": {
                          "aggregate_rating": float,
                          "review_count": int
                      }
                    }
                On failure:
                    {
                      "success": False,
                      "error": str  # Reason, e.g. provider not found
                    }

        Constraints:
            - provider_id must exist in the system.
        """
        provider = self.providers.get(provider_id)
        if not provider:
            return { "success": False, "error": "Provider not found" }
        return {
            "success": True,
            "data": {
                "aggregate_rating": provider["aggregate_rating"],
                "review_count": provider["review_count"]
            }
        }

    def get_reviews_with_status(
        self,
        status: str,
        provider_id: str = None,
        user_id: str = None
    ) -> dict:
        """
        List reviews for a provider or user, filtered by moderation status.

        Args:
            status (str): Moderation/review status to filter by (e.g., 'approved', 'pending', 'rejected').
            provider_id (str, optional): If provided, restrict results to this provider.
            user_id (str, optional): If provided, restrict results to this user.

        Returns:
            dict: {
                "success": True,
                "data": List[ReviewInfo]
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - At least one of provider_id or user_id must be provided.
            - If provided, provider_id/user_id must exist in the system.
            - status must not be empty.
        """
        # Basic validation
        if not status or not status.strip():
            return {"success": False, "error": "Status value must be provided and non-empty."}
        normalized_provider_id = provider_id
        normalized_user_id = user_id
        if isinstance(normalized_provider_id, str) and not normalized_provider_id.strip():
            normalized_provider_id = None
        if isinstance(normalized_user_id, str) and not normalized_user_id.strip():
            normalized_user_id = None

        if normalized_provider_id is None and normalized_user_id is None:
            return {"success": False, "error": "At least one of provider_id or user_id must be specified."}
        if normalized_provider_id is not None and normalized_provider_id not in self.providers:
            return {"success": False, "error": f"Provider {normalized_provider_id} does not exist."}
        if normalized_user_id is not None and normalized_user_id not in self.users:
            return {"success": False, "error": f"User {normalized_user_id} does not exist."}

        # Filter reviews
        filtered_reviews = []
        for review in self.reviews.values():
            if review["status"] != status:
                continue
            if normalized_provider_id is not None and review["provider_id"] != normalized_provider_id:
                continue
            if normalized_user_id is not None and review["user_id"] != normalized_user_id:
                continue
            filtered_reviews.append(review)

        return {"success": True, "data": filtered_reviews}

    def add_review(
        self,
        review_id: str,
        provider_id: str,
        user_id: str,
        rating: float,
        review_text: str,
        submission_date: str,
        status: str = "active",
        max_review_length: int = 1000,
        restrict_duplicates: bool = True
    ) -> dict:
        """
        Create a new review for a provider by a user. Updates provider’s aggregate rating and review count.

        Args:
            review_id (str): Unique ID for the new review.
            provider_id (str): The provider to be reviewed (must exist).
            user_id (str): The user submitting the review (must exist).
            rating (float): Rating value (must be in [1.0, 5.0]).
            review_text (str): The body of the review, subject to length.
            submission_date (str): Submission timestamp (string).
            status (str, optional): Moderation status. Default is 'active'.
            max_review_length (int, optional): Max allowable review text length.
            restrict_duplicates (bool, optional): If True, restrict user to one review per provider.

        Returns:
            dict: On success:
                {"success": True, "message": "Review added successfully and aggregate rating updated."}
            On failure:
                {"success": False, "error": <reason string>}

        Constraints:
            - provider_id and user_id must exist.
            - rating must be within [1.0, 5.0].
            - review_id must be unique.
            - Optionally, enforce one review per user per provider.
            - Review text length must not exceed max_review_length.
            - Updates aggregate_rating and review_count of provider after addition.
        """
        # Check provider exists
        if provider_id not in self.providers:
            return {"success": False, "error": "Provider does not exist."}

        # Check user exists
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist."}

        # Check review_id is unique
        if review_id in self.reviews:
            return {"success": False, "error": "Review ID already exists."}

        # Check rating is in range
        if not (1.0 <= rating <= 5.0):
            return {"success": False, "error": "Rating must be between 1.0 and 5.0."}

        # Review text constraints
        if len(review_text) == 0 or len(review_text) > max_review_length:
            return {"success": False, "error": f"Review text must be 1 to {max_review_length} characters."}

        # Optionally restrict duplicate reviews from same user for the provider
        if restrict_duplicates:
            for r in self.reviews.values():
                if r["provider_id"] == provider_id and r["user_id"] == user_id:
                    return {"success": False, "error": "Duplicate review: user has already reviewed this provider."}

        # Create new review entry
        new_review = {
            "review_id": review_id,
            "provider_id": provider_id,
            "user_id": user_id,
            "rating": rating,
            "review_text": review_text,
            "submission_date": submission_date,
            "status": status,
        }
        self.reviews[review_id] = new_review

        self._recompute_provider_aggregate(provider_id)

        return {
            "success": True,
            "message": "Review added successfully and aggregate rating updated."
        }

    def edit_review(
        self,
        review_id: str,
        rating: float = None,
        review_text: str = None,
        new_rating: float = None,
        updated_review_text: str = None
    ) -> dict:
        """
        Modify the rating and/or review text of an existing review.
        Updates provider's aggregate rating/statistics if rating changes.

        Args:
            review_id (str): The review to edit (must exist).
            rating (Optional[float]): New rating (must be 1.0–5.0 if supplied).
            review_text (Optional[str]): New review text (subject to optional max length).

        Returns:
            dict: {
                "success": True,
                "message": "Review updated successfully"
            }
            or
            {
                "success": False,
                "error": error_message
            }

        Constraints:
            - Review must exist and not be deleted.
            - New rating, if given, must be 1.0–5.0.
            - Provider must exist.
            - Optionally enforce a review_text length limit (e.g., 2000).
            - Provider's aggregate rating & review count must be updated if rating is changed.
        """
        if rating is None and new_rating is not None:
            rating = new_rating
        if review_text is None and updated_review_text is not None:
            review_text = updated_review_text

        # Review existence check
        review = self.reviews.get(review_id)
        if not review:
            return { "success": False, "error": "Review not found" }

        # Prevent editing deleted reviews
        if review.get("status") == "deleted":
            return { "success": False, "error": "Cannot edit a deleted review" }

        updated = False
        old_rating = review["rating"]

        # Update rating if supplied
        if rating is not None:
            if not (1.0 <= rating <= 5.0):
                return { "success": False, "error": "Rating must be between 1.0 and 5.0" }
            if rating != review["rating"]:
                review["rating"] = rating
                updated = True

        # Update review_text if supplied
        if review_text is not None:
            # Character limit (assume 2000, can be adjusted)
            if len(review_text) > 2000:
                return { "success": False, "error": "Review text exceeds character limit" }
            if review_text != review["review_text"]:
                review["review_text"] = review_text
                updated = True

        if not updated:
            return { "success": False, "error": "No changes to apply" }

        # Update review in self.reviews (dict is mutable, so changes already in-place)

        # Provider aggregate update (if rating modified)
        provider_id = review["provider_id"]
        provider = self.providers.get(provider_id)
        if not provider:
            return { "success": False, "error": "Provider for this review does not exist" }

        # Always update aggregate if rating changed
        if rating is not None and rating != old_rating:
            aggregate, count = self._recompute_provider_aggregate(provider_id)
            provider["aggregate_rating"] = aggregate
            provider["review_count"] = count

        return { "success": True, "message": "Review updated successfully" }

    def delete_review(self, review_id: str) -> dict:
        """
        Remove a review by its review_id and update the provider’s aggregate rating and review count.

        Args:
            review_id (str): The unique identifier of the review to be deleted.

        Returns:
            dict: {
                "success": True,
                "message": "Review deleted and provider statistics updated."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The review must exist.
            - The provider referenced by the review must exist.
            - After deletion, provider's aggregate_rating and review_count are recomputed
              (if no remaining reviews: aggregate_rating is 0.0, review_count is 0).
        """
        # Check if review exists
        review_info = self.reviews.get(review_id)
        if not review_info:
            return {"success": False, "error": "Review does not exist."}

        provider_id = review_info["provider_id"]

        # Remove the review
        del self.reviews[review_id]

        # Make sure provider exists
        provider_info = self.providers.get(provider_id)
        if not provider_info:
            return {"success": False, "error": "Provider does not exist for this review."}

        # Recompute aggregate rating and review count
        new_aggregate_rating, review_count = self._recompute_provider_aggregate(provider_id)
        provider_info["aggregate_rating"] = new_aggregate_rating
        provider_info["review_count"] = review_count
        self.providers[provider_id] = provider_info

        return {
            "success": True,
            "message": "Review deleted and provider statistics updated."
        }

    def moderate_review(self, review_id: str, new_status: str) -> dict:
        """
        Update the status of a specified review (moderate, flag, or mark as removed/published/etc.).

        Args:
            review_id (str): The unique identifier of the review to update.
            new_status (str): The new status to assign (e.g., 'moderated', 'pending', 'published', 'removed', etc.).

        Returns:
            dict: 
                On success:
                    { "success": True, "message": "Review status updated to <new_status>" }
                On failure (review not found):
                    { "success": False, "error": "Review does not exist" }

        Constraints:
            - The review must exist.
            - No restriction is specified for allowed statuses.
        """
        if review_id not in self.reviews:
            return { "success": False, "error": "Review does not exist" }

        self.reviews[review_id]['status'] = new_status
        return { "success": True, "message": f"Review status updated to {new_status}" }

    def update_provider_aggregate(self, provider_id: str) -> dict:
        """
        Recompute and update the aggregate_rating and review_count for the given provider.

        Args:
            provider_id (str): The provider for whom to update aggregate values.

        Returns:
            dict: {
                "success": True,
                "message": "Aggregate rating and review count updated for provider <provider_id>"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Provider must exist.
            - Only reviews with the given provider_id are counted.
            - If there are no reviews, aggregate_rating is set to 0.0 and review_count is 0.
            - (If review status is relevant, update accordingly.)
        """
        provider = self.providers.get(provider_id)
        if provider is None:
            return {"success": False, "error": "Provider not found"}

        # Update the provider's info
        aggregate_rating, review_count = self._recompute_provider_aggregate(provider_id)
        provider["aggregate_rating"] = aggregate_rating
        provider["review_count"] = review_count
        self.providers[provider_id] = provider

        return {
            "success": True,
            "message": f"Aggregate rating and review count updated for provider {provider_id}"
        }

    def restore_review(self, review_id: str) -> dict:
        """
        Reinstate a previously deleted or hidden review, adjusting provider aggregates accordingly.

        Args:
            review_id (str): The ID of the review to reinstate.

        Returns:
            dict:
                On success: { 'success': True, 'message': 'Review restored and aggregates updated.' }
                On failure: { 'success': False, 'error': <reason str> }

        Constraints:
            - The review and corresponding provider must exist.
            - Only restores a review that is currently not active/visible.
            - Updates the provider's aggregate_rating and review_count after restoration.
        """
        # Check review existence
        review = self.reviews.get(review_id)
        if not review:
            return { "success": False, "error": "Review does not exist." }

        # Only restore if not already active/visible
        if review.get("status", "").lower() in ("active", "visible"):
            return { "success": False, "error": "Review is already active." }

        provider_id = review.get("provider_id")
        provider = self.providers.get(provider_id)
        if not provider:
            return { "success": False, "error": "Associated provider does not exist." }

        # Restore review (set status to 'active')
        review["status"] = "active"

        aggregate_rating, review_count = self._recompute_provider_aggregate(provider_id)
        provider["aggregate_rating"] = aggregate_rating
        provider["review_count"] = review_count

        return { "success": True, "message": "Review restored and aggregates updated." }


class HealthcareProviderReviewManagementSystem(BaseEnv):
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

    def get_provider_by_name(self, **kwargs):
        return self._call_inner_tool('get_provider_by_name', kwargs)

    def get_provider_by_id(self, **kwargs):
        return self._call_inner_tool('get_provider_by_id', kwargs)

    def list_all_providers(self, **kwargs):
        return self._call_inner_tool('list_all_providers', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def get_user_by_name(self, **kwargs):
        return self._call_inner_tool('get_user_by_name', kwargs)

    def check_user_account_status(self, **kwargs):
        return self._call_inner_tool('check_user_account_status', kwargs)

    def list_reviews_for_provider(self, **kwargs):
        return self._call_inner_tool('list_reviews_for_provider', kwargs)

    def list_reviews_by_user(self, **kwargs):
        return self._call_inner_tool('list_reviews_by_user', kwargs)

    def get_review_by_id(self, **kwargs):
        return self._call_inner_tool('get_review_by_id', kwargs)

    def check_duplicate_review(self, **kwargs):
        return self._call_inner_tool('check_duplicate_review', kwargs)

    def get_provider_aggregate_rating(self, **kwargs):
        return self._call_inner_tool('get_provider_aggregate_rating', kwargs)

    def get_reviews_with_status(self, **kwargs):
        return self._call_inner_tool('get_reviews_with_status', kwargs)

    def add_review(self, **kwargs):
        return self._call_inner_tool('add_review', kwargs)

    def edit_review(self, **kwargs):
        return self._call_inner_tool('edit_review', kwargs)

    def delete_review(self, **kwargs):
        return self._call_inner_tool('delete_review', kwargs)

    def moderate_review(self, **kwargs):
        return self._call_inner_tool('moderate_review', kwargs)

    def update_provider_aggregate(self, **kwargs):
        return self._call_inner_tool('update_provider_aggregate', kwargs)

    def restore_review(self, **kwargs):
        return self._call_inner_tool('restore_review', kwargs)
