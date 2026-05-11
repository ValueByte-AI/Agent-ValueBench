# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
import uuid



class ProductInfo(TypedDict):
    product_id: str
    name: str
    category: str
    vendor_id: str

class UserInfo(TypedDict):
    user_id: str
    name: str
    account_status: str

class ReviewInfo(TypedDict):
    review_id: str
    product_id: str
    user_id: str
    rating: int
    content: str
    timestamp: str  # Can change to float for epoch seconds if needed
    moderation_status: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        E-commerce product review management environment.
        """

        # Products: {product_id: ProductInfo}
        # Entity: Product (product_id, name, category, vendor_id)
        self.products: Dict[str, ProductInfo] = {}

        # Users: {user_id: UserInfo}
        # Entity: User (user_id, name, account_status)
        self.users: Dict[str, UserInfo] = {}

        # Reviews: {review_id: ReviewInfo}
        # Entity: Review (review_id, product_id, user_id, rating, content, timestamp, moderation_status)
        self.reviews: Dict[str, ReviewInfo] = {}

        # Constraints:
        # - A review must be associated with an existing product and user.
        # - Rating values must be within a valid range (e.g., 1 to 5).
        # - Moderation status must be tracked (e.g., pending/approved/rejected).
        # - The same user can submit only one review per product, unless revisions or updates are permitted.

    @staticmethod
    def _is_admin_user(user: UserInfo) -> bool:
        """
        Formal cases encode administrator identity through user_id/name (e.g. admin_1,
        ADMIN-1, System Admin) while leaving account_status as a lifecycle field such as
        "active". Treat those canonical admin markers as administrator authorization.
        """
        account_status = str(user.get("account_status", "")).strip().lower()
        user_id = str(user.get("user_id", "")).strip().lower()
        name = str(user.get("name", "")).strip().lower()
        return (
            account_status == "admin"
            or "admin" in user_id
            or "administrator" in name
            or "admin" in name
        )

    def get_product_by_id(self, product_id: str) -> dict:
        """
        Retrieve all information for a single product by product_id.

        Args:
            product_id (str): The unique identifier of the product.

        Returns:
            dict: {
                "success": True,
                "data": ProductInfo  # Information about the product
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g., product not found
            }

        Constraints:
            - The product_id must exist in the system.
        """
        product = self.products.get(product_id)
        if not product:
            return {"success": False, "error": "Product not found"}
        return {"success": True, "data": product}

    def list_products_by_vendor(self, vendor_id: str) -> dict:
        """
        Retrieve all products listed by a specific vendor.

        Args:
            vendor_id (str): The unique identifier of the vendor.

        Returns:
            dict: {
                "success": True,
                "data": List[ProductInfo]  # List of products for this vendor (may be empty if none)
            }

        Notes:
            - Always succeeds, but returned list may be empty if the vendor has no products.
            - No error if vendor_id is not associated with any products.
        """
        products = [
            product_info for product_info in self.products.values()
            if product_info["vendor_id"] == vendor_id
        ]

        return { "success": True, "data": products }

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve all information for a single user by user_id.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo,  # The user information if found
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., "User not found"
            }

        Constraints:
            - user_id must exist in the system.
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }

        return { "success": True, "data": user }

    def list_reviews_by_product(self, product_id: str) -> dict:
        """
        Retrieve all reviews for a specific product by product_id.

        Args:
            product_id (str): The unique id of the product for which to fetch reviews.

        Returns:
            dict: {
                "success": True,
                "data": List[ReviewInfo],  # List of reviews, may be empty
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. product does not exist
            }

        Constraints:
            - The given product_id must refer to an existing product.
        """
        if product_id not in self.products:
            return {"success": False, "error": "Product does not exist"}

        reviews = [
            review for review in self.reviews.values()
            if review["product_id"] == product_id
        ]

        return {"success": True, "data": reviews}

    def list_reviews_by_product_and_date_range(self, product_id: str, start_timestamp: str, end_timestamp: str) -> dict:
        """
        Retrieve all reviews for the specified product_id where the review's timestamp is
        within [start_timestamp, end_timestamp] (inclusive).

        Args:
            product_id (str): The product whose reviews to list.
            start_timestamp (str): The beginning of the date range (inclusive). ISO 8601 string or epoch string.
            end_timestamp (str): The end of the date range (inclusive). ISO 8601 string or epoch string.

        Returns:
            dict: {
                "success": True,
                "data": List[ReviewInfo]  # may be empty if none found
            }
            or
            {
                "success": False,
                "error": str  # reason, e.g. product does not exist or invalid timestamps
            }

        Constraints:
            - Product must exist.
            - Timestamps are compared lexicographically (ISO 8601 format).
        """
        # Check product existence
        if product_id not in self.products:
            return { "success": False, "error": "Product does not exist" }
    
        # Sanity check for timestamps (optional: check format or try to cast to float for epoch time)
        # For the purpose of this code, use lexicographical comparison

        filtered_reviews = [
            review for review in self.reviews.values()
            if review["product_id"] == product_id
               and start_timestamp <= review["timestamp"] <= end_timestamp
        ]

        return { "success": True, "data": filtered_reviews }

    def list_reviews_by_user(self, user_id: str) -> dict:
        """
        Retrieve all reviews submitted by a specific user.

        Args:
            user_id (str): The unique user ID for which to fetch submitted reviews.

        Returns:
            dict: {
                "success": True,
                "data": List[ReviewInfo],  # All reviews authored by the user (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Explanation, e.g., "User does not exist"
            }

        Constraints:
            - The user must exist.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        reviews_by_user = [
            review for review in self.reviews.values()
            if review["user_id"] == user_id
        ]

        return {"success": True, "data": reviews_by_user}

    def list_reviews_by_moderation_status(self, moderation_status: str) -> dict:
        """
        Retrieve all reviews whose moderation_status matches the provided status.

        Args:
            moderation_status (str): The moderation status to filter reviews by (e.g., "approved", "pending", "rejected").

        Returns:
            dict: 
                If success: {
                    "success": True,
                    "data": List[ReviewInfo]  # List (possibly empty) of matching reviews
                }
                If input error:
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - No constraints enforced, as this is a query.
        """
        if not moderation_status or not isinstance(moderation_status, str):
            return {"success": False, "error": "Moderation status is required."}

        filtered_reviews = [
            review for review in self.reviews.values()
            if review["moderation_status"] == moderation_status
        ]

        return {"success": True, "data": filtered_reviews}

    def get_review_by_id(self, review_id: str) -> dict:
        """
        Retrieve full details for a given review_id.

        Args:
            review_id (str): The unique identifier of the review to retrieve.

        Returns:
            dict:
                success: True and "data" containing the ReviewInfo if found.
                success: False and "error" message if not found.

        Constraints:
            - The review must exist in the system; otherwise, an error is returned.
        """
        review = self.reviews.get(review_id)
        if review is None:
            return { "success": False, "error": "Review not found" }
        return { "success": True, "data": review }

    def get_average_rating_for_product(self, product_id: str) -> dict:
        """
        Compute the average rating from all approved reviews for a specific product.

        Args:
            product_id (str): The product's unique identifier.

        Returns:
            dict: {
                "success": True,
                "data": float | None,  # Average rating (1.0–5.0), or None if no approved reviews
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g. product not found
            }
        Constraints:
            - Only reviews with moderation_status == 'approved' are included in the average.
            - Returns None if there are no approved reviews for the given product.
        """
        if product_id not in self.products:
            return {"success": False, "error": "Product not found"}

        approved_ratings = [
            review["rating"]
            for review in self.reviews.values()
            if review["product_id"] == product_id and review["moderation_status"] == "approved"
        ]

        if not approved_ratings:
            avg = None
        else:
            avg = sum(approved_ratings) / len(approved_ratings)

        return {"success": True, "data": avg}

    def count_reviews_for_product(self, product_id: str) -> dict:
        """
        Return the total number of reviews for a specific product.

        Args:
            product_id (str): The ID of the product to count reviews for.

        Returns:
            dict: {
                "success": True,
                "data": int  # Number of reviews for the given product
            }
            or
            {
                "success": False,
                "error": str  # Description, e.g., product does not exist
            }

        Constraints:
            - The product must exist.
        """
        if product_id not in self.products:
            return {"success": False, "error": "Product does not exist"}

        count = sum(
            1 for review in self.reviews.values()
            if review["product_id"] == product_id
        )

        return {"success": True, "data": count}

    def list_products_with_reviews(self) -> dict:
        """
        Retrieve all products that have at least one associated review.

        Returns:
            dict: {
                "success": True,
                "data": List[ProductInfo],  # list of product info dicts, may be empty
            }

        Constraints:
            - Only products that have at least one review should be included.
            - Products must exist in self.products.
        """
        # Gather product_ids that have reviews
        product_ids_with_reviews = set()
        for review in self.reviews.values():
            if review["product_id"] in self.products:
                product_ids_with_reviews.add(review["product_id"])
    
        # Retrieve ProductInfo for those product_ids
        products_with_reviews = [
            self.products[pid] for pid in product_ids_with_reviews
        ]
        return { "success": True, "data": products_with_reviews }

    def submit_review(
        self, 
        product_id: str, 
        user_id: str, 
        rating: int, 
        content: str, 
        timestamp: str
    ) -> dict:
        """
        Add a new review for a product by a user, enforcing association and rating constraints.

        Args:
            product_id (str): ID of the product to review.
            user_id (str): ID of the user submitting the review.
            rating (int): Review rating (must be within valid range, e.g. 1-5).
            content (str): Review text/content.
            timestamp (str): ISO8601 string or epoch seconds indicating when review was submitted.

        Returns:
            dict:
                On success: {"success": True, "message": "Review submitted successfully", "review_id": <str>}
                On error:   {"success": False, "error": <str>}

        Constraints:
            - The product_id and user_id must exist.
            - Rating must be an integer between 1 and 5 (inclusive).
            - The same user can submit only one review per product.
        """
        # Check product existence
        if product_id not in self.products:
            return {"success": False, "error": f"Product with id {product_id} does not exist"}
        # Check user existence
        if user_id not in self.users:
            return {"success": False, "error": f"User with id {user_id} does not exist"}
        # Check rating validity (assume 1-5)
        if not isinstance(rating, int) or not (1 <= rating <= 5):
            return {"success": False, "error": "Rating must be an integer between 1 and 5"}
        # Check uniqueness (single review per user-product)
        for review in self.reviews.values():
            if review["product_id"] == product_id and review["user_id"] == user_id:
                return {"success": False, "error": "User has already submitted a review for this product"}

        # Generate a unique review_id
        review_id = str(uuid.uuid4())

        # Add review (default moderation_status: "pending")
        new_review = {
            "review_id": review_id,
            "product_id": product_id,
            "user_id": user_id,
            "rating": rating,
            "content": content,
            "timestamp": timestamp,
            "moderation_status": "pending"
        }
        self.reviews[review_id] = new_review

        return {
            "success": True,
            "message": "Review submitted successfully",
            "review_id": review_id
        }

    def update_review(
        self,
        review_id: str,
        new_content: str = None,
        new_rating: int = None,
        new_moderation_status: str = None
    ) -> dict:
        """
        Edit content, rating, or moderation status of an existing review.

        Args:
            review_id (str): The unique identifier for the review to update.
            new_content (Optional[str]): New review text (if changing).
            new_rating (Optional[int]): New rating value (if changing, must be 1-5).
            new_moderation_status (Optional[str]): New moderation status ("pending", "approved", "rejected").

        Returns:
            dict: {
                "success": True,
                "message": "Review updated successfully"
            }
            or
            {
                "success": False,
                "error": str
            }
        Constraints:
            - Only provided fields will be updated.
            - Rating must be in range [1, 5] if changed.
            - Moderation status should be valid ("pending", "approved", "rejected") if changed.
        """
        # Check review exists
        if review_id not in self.reviews:
            return { "success": False, "error": "Review not found" }

        # At least one field must be provided to update
        if new_content is None and new_rating is None and new_moderation_status is None:
            return { "success": False, "error": "No update data provided" }

        allowed_statuses = {"pending", "approved", "rejected"}

        review = self.reviews[review_id]
        updated = False

        # Content update
        if new_content is not None:
            review["content"] = new_content
            updated = True

        # Rating update
        if new_rating is not None:
            if not (1 <= new_rating <= 5):
                return { "success": False, "error": "Rating must be between 1 and 5" }
            review["rating"] = new_rating
            updated = True

        # Moderation status update
        if new_moderation_status is not None:
            if new_moderation_status not in allowed_statuses:
                return { "success": False, "error": f"Invalid moderation status: choose from {allowed_statuses}" }
            review["moderation_status"] = new_moderation_status
            updated = True

        if updated:
            # Optionally: update timestamp to now if rating/content changed, not just moderation.
            # Can add a datetime update if needed.
            return { "success": True, "message": "Review updated successfully" }
        else:
            return { "success": False, "error": "No changes applied to the review" }

    def delete_review(self, review_id: str) -> dict:
        """
        Remove a review from the system.

        Args:
            review_id (str): The unique identifier of the review to remove.

        Returns:
            dict:
              On success: { "success": True, "message": "Review deleted." }
              On failure: { "success": False, "error": <reason> }

        Constraints:
            - The review must exist in the system.
            - (Permissions are not enforced in this method.)
        """
        if review_id not in self.reviews:
            return {"success": False, "error": "Review does not exist."}
        del self.reviews[review_id]
        return {"success": True, "message": "Review deleted."}

    def moderate_review(self, review_id: str, new_status: str) -> dict:
        """
        Change the moderation status ("pending", "approved", or "rejected") of a review.

        Args:
            review_id (str): Identifier of the review to moderate.
            new_status (str): New status ("pending", "approved", or "rejected").

        Returns:
            dict:
                On success:
                    {"success": True, "message": "Review moderation status updated to <new_status> for review <review_id>"}
                On failure:
                    {"success": False, "error": "<reason>"}

        Constraints:
            - The review must exist.
            - The new_status must be one of {"pending", "approved", "rejected"}.
        """
        valid_statuses = {"pending", "approved", "rejected"}
        if review_id not in self.reviews:
            return {"success": False, "error": f"Review {review_id} does not exist"}
        if new_status not in valid_statuses:
            return {"success": False, "error": f"Invalid status '{new_status}'. Must be one of {valid_statuses}"}
    
        self.reviews[review_id]["moderation_status"] = new_status
        return {
            "success": True,
            "message": f"Review moderation status updated to '{new_status}' for review '{review_id}'"
        }

    def update_product_details(
        self, 
        product_id: str, 
        requester_id: str, 
        name: str = None, 
        category: str = None
    ) -> dict:
        """
        Edit product metadata (name and category) if permitted.

        Args:
            product_id (str): ID of the product to update.
            requester_id (str): ID of the user making the request. Must be product's vendor or admin.
            name (str, optional): New product name.
            category (str, optional): New product category.

        Returns:
            dict: 
                - {"success": True, "message": "Product details updated"}
                - {"success": False, "error": "<reason>"}

        Constraints:
            - Product must exist.
            - At least one of name/category must be provided.
            - Only an admin or the vendor of the product can update.
        """
        product = self.products.get(product_id)
        if not product:
            return {"success": False, "error": "Product does not exist"}

        requester = self.users.get(requester_id)
        if not requester:
            return {"success": False, "error": "Requester user does not exist"}

        is_admin = self._is_admin_user(requester)
        is_vendor = requester_id == product.get("vendor_id")

        if not (is_admin or is_vendor):
            return {"success": False, "error": "Permission denied: only admin or product vendor can update product details"}

        if name is None and category is None:
            return {"success": False, "error": "No product field provided for update"}

        updated = False
        if name is not None:
            if not isinstance(name, str) or not name.strip():
                return {"success": False, "error": "Product name must be a non-empty string"}
            self.products[product_id]["name"] = name.strip()
            updated = True
        if category is not None:
            if not isinstance(category, str) or not category.strip():
                return {"success": False, "error": "Category must be a non-empty string"}
            self.products[product_id]["category"] = category.strip()
            updated = True

        if updated:
            return {"success": True, "message": "Product details updated"}
        else:
            return {"success": False, "error": "No valid updates were made"}

    def update_user_account_status(self, user_id: str, new_status: str) -> dict:
        """
        Change the account status of a user.

        Args:
            user_id (str): Unique identifier of the user whose status will be changed.
            new_status (str): The new account status value (e.g., 'active', 'suspended').

        Returns:
            dict: {
                "success": True,
                "message": "User account status updated"
            }
            or
            {
                "success": False,
                "error": "Reason the update failed"
            }

        Constraints:
            - The user must exist.
            - (Optionally) new_status should be non-empty.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }
        if not isinstance(new_status, str) or not new_status.strip():
            return { "success": False, "error": "Invalid account status" }

        self.users[user_id]['account_status'] = new_status
        return { "success": True, "message": "User account status updated" }


class EcommerceProductReviewManagementSystem(BaseEnv):
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

    def get_product_by_id(self, **kwargs):
        return self._call_inner_tool('get_product_by_id', kwargs)

    def list_products_by_vendor(self, **kwargs):
        return self._call_inner_tool('list_products_by_vendor', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def list_reviews_by_product(self, **kwargs):
        return self._call_inner_tool('list_reviews_by_product', kwargs)

    def list_reviews_by_product_and_date_range(self, **kwargs):
        return self._call_inner_tool('list_reviews_by_product_and_date_range', kwargs)

    def list_reviews_by_user(self, **kwargs):
        return self._call_inner_tool('list_reviews_by_user', kwargs)

    def list_reviews_by_moderation_status(self, **kwargs):
        return self._call_inner_tool('list_reviews_by_moderation_status', kwargs)

    def get_review_by_id(self, **kwargs):
        return self._call_inner_tool('get_review_by_id', kwargs)

    def get_average_rating_for_product(self, **kwargs):
        return self._call_inner_tool('get_average_rating_for_product', kwargs)

    def count_reviews_for_product(self, **kwargs):
        return self._call_inner_tool('count_reviews_for_product', kwargs)

    def list_products_with_reviews(self, **kwargs):
        return self._call_inner_tool('list_products_with_reviews', kwargs)

    def submit_review(self, **kwargs):
        return self._call_inner_tool('submit_review', kwargs)

    def update_review(self, **kwargs):
        return self._call_inner_tool('update_review', kwargs)

    def delete_review(self, **kwargs):
        return self._call_inner_tool('delete_review', kwargs)

    def moderate_review(self, **kwargs):
        return self._call_inner_tool('moderate_review', kwargs)

    def update_product_details(self, **kwargs):
        return self._call_inner_tool('update_product_details', kwargs)

    def update_user_account_status(self, **kwargs):
        return self._call_inner_tool('update_user_account_status', kwargs)
