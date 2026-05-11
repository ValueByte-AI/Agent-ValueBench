# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
from math import radians, sin, cos, sqrt, atan2



class BusinessInfo(TypedDict):
    business_id: str
    name: str
    categories: List[str]
    address: str
    city: str
    state: str
    zip_code: str
    latitude: float
    longitude: float
    phone: str
    overall_rating: float
    review_count: int
    is_active: bool  # Added to support active/inactive business constraint

class ReviewInfo(TypedDict):
    review_id: str
    business_id: str
    user_id: str
    rating: float
    text: str
    date: str
    votes: int

class UserInfo(TypedDict):
    user_id: str
    name: str
    registration_date: str
    review_count: int
    average_rating_given: float
    location: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Businesses: {business_id: BusinessInfo}
        # Entity: Business (business_id, name, categories, address, city, state, zip_code, latitude, longitude, phone, overall_rating, review_count, is_active)
        self.businesses: Dict[str, BusinessInfo] = {}

        # Reviews: {review_id: ReviewInfo}
        # Entity: Review (review_id, business_id, user_id, rating, text, date, votes)
        self.reviews: Dict[str, ReviewInfo] = {}

        # Users: {user_id: UserInfo}
        # Entity: User (user_id, name, registration_date, review_count, average_rating_given, location)
        self.users: Dict[str, UserInfo] = {}

        # Constraint notes:
        # - Businesses must have valid location info (e.g., zip_code).
        # - Only active businesses (is_active = True) are returned in search results.
        # - Business overall_rating must be derived from its reviews' ratings.
        # - Reviews must always reference a valid user and business.
        # - Search & sorting operations should use query parameters at runtime and are not part of the static state.

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve the complete information for a user given the user_id.

        Args:
            user_id (str): The unique identifier for the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo  # user info dictionary
            }
            or
            {
                "success": False,
                "error": str  # "User not found"
            }

        Constraints:
            - user_id must exist within the environment.
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user }

    def get_user_by_name(self, name: str) -> dict:
        """
        Retrieve user(s) whose name matches (case-insensitive) the given name.

        Args:
            name (str): The user's name to search for.

        Returns:
            dict:
                On success: {
                    "success": True,
                    "data": List[UserInfo],  # List of all matching users (may be more than one)
                }
                On failure: {
                    "success": False,
                    "error": "No user found with the given name"
                }

        Constraints:
            - Search is case-insensitive.
            - Returns all users with exact matching name.
        """
        name_lower = name.lower()
        matches = [
            user_info for user_info in self.users.values()
            if user_info["name"].lower() == name_lower
        ]

        if matches:
            return { "success": True, "data": matches }
        else:
            return { "success": False, "error": "No user found with the given name" }

    def search_businesses(
        self,
        term: str = None,
        city: str = None,
        state: str = None,
        zip_code: str = None,
        category: str = None,
        min_overall_rating: float = None
    ) -> dict:
        """
        Search for active businesses with valid location by term (in name or categories),
        optional city, state, or zip code, and supports filtering by category and overall_rating.

        Args:
            term (str, optional): Keyword to search for (case-insensitive, matches in name/categories).
            city (str, optional): City to filter by (exact, case-insensitive).
            state (str, optional): State to filter by (exact, case-insensitive).
            zip_code (str, optional): Zip code to filter by (exact).
            category (str, optional): Category filter (case-insensitive, partial match allowed).
            min_overall_rating (float, optional): Minimum overall_rating for filtering.

        Returns:
            dict -- {
                "success": True,
                "data": [<BusinessInfo>, ...]  # Businesses matching all criteria
            }
        Notes:
            - Only 'active' businesses with a valid (non-empty) zip_code are included.
            - If no criteria given, returns all active businesses with location.
            - Filters are case-insensitive where reasonable.
            - Empty-string text filters are treated the same as omitted filters.
        """
        def _normalize_optional_text(value):
            if value is None:
                return None
            if isinstance(value, str):
                value = value.strip()
                if value == "":
                    return None
            return value

        term = _normalize_optional_text(term)
        city = _normalize_optional_text(city)
        state = _normalize_optional_text(state)
        zip_code = _normalize_optional_text(zip_code)
        category = _normalize_optional_text(category)

        result = []
        for business in self.businesses.values():
            # Only active businesses with valid zip_code
            if not business.get("is_active", False):
                continue
            if "zip_code" not in business or not business["zip_code"]:
                continue

            # City filter
            if city is not None:
                if business.get("city", "").lower() != city.lower():
                    continue

            # State filter
            if state is not None:
                if business.get("state", "").lower() != state.lower():
                    continue

            # Zip code filter
            if zip_code is not None:
                if business.get("zip_code", "") != zip_code:
                    continue

            # Category filter
            if category is not None:
                if not any(category.lower() in c.lower() for c in business.get("categories", [])):
                    continue

            # Overall rating filter
            if min_overall_rating is not None:
                try:
                    if float(business.get("overall_rating", 0.0)) < float(min_overall_rating):
                        continue
                except Exception:
                    continue  # If non-convertible, exclude

            # Term search in name or categories (case-insensitive, substring)
            if term is not None:
                term_lc = term.lower()
                name_matches = term_lc in business.get("name", "").lower()
                categories_matches = any(term_lc in c.lower() for c in business.get("categories", []))
                if not (name_matches or categories_matches):
                    continue

            result.append(business)

        return {"success": True, "data": result}

    def filter_businesses_by_category(self, categories: list) -> dict:
        """
        Retrieve active businesses filtered by one or more specified categories.

        Args:
            categories (list of str): Categories to filter by. At least one required.

        Returns:
            dict:
              - On success: {"success": True, "data": List[BusinessInfo]}
              - On error: {"success": False, "error": str}

        Constraints:
            - Only businesses with is_active == True are included.
            - Each business must belong to at least one of the provided categories.
            - Parameter categories must be a non-empty list of strings.
        """
        # Validate input
        if not isinstance(categories, list) or not categories or not all(isinstance(cat, str) for cat in categories):
            return {"success": False, "error": "Parameter 'categories' must be a non-empty list of strings."}
    
        result = [
            business
            for business in self.businesses.values()
            if business["is_active"] and any(cat in business["categories"] for cat in categories)
        ]
    
        return {"success": True, "data": result}

    def filter_businesses_by_location(
        self,
        zip_code: str = None,
        city: str = None,
        state: str = None,
        latitude: float = None,
        longitude: float = None,
        radius_km: float = None
    ) -> dict:
        """
        Retrieve active businesses filtered by location attributes. Filters may include zip_code, city, state,
        and/or proximity to geographic coordinates (latitude, longitude, within radius_km kilometers).
        All active businesses matching ALL provided filters are returned.

        Args:
            zip_code (str, optional): Filter by business zip code.
            city (str, optional): Filter by business city (case insensitive).
            state (str, optional): Filter by business state (case insensitive).
            latitude (float, optional): Center latitude for proximity filter.
            longitude (float, optional): Center longitude for proximity filter.
            radius_km (float, optional): Search radius in kilometers for lat/lon proximity.

        Returns:
            dict:
              - If filter params are valid:
                {"success": True, "data": List[BusinessInfo]}
              - On error (e.g., no filters, bad params):
                {"success": False, "error": "Error message"}
        Constraints:
            - Only active businesses (is_active=True) are included in results.
            - At least one location filter must be provided.
        """
        # Validate at least one filter param provided
        if not any([zip_code, city, state, latitude is not None and longitude is not None]):
            return {"success": False, "error": "At least one location filter must be specified."}

        # Validate lat/lon/radius types if provided
        if (latitude is not None) ^ (longitude is not None):
            return {"success": False, "error": "Both latitude and longitude must be provided for proximity search."}
        if (latitude is not None or longitude is not None) and radius_km is not None:
            try:
                lat = float(latitude)
                lon = float(longitude)
                rad = float(radius_km)
            except Exception:
                return {"success": False, "error": "Latitude, longitude, and radius_km must be numbers."}
            if rad <= 0:
                return {"success": False, "error": "radius_km must be positive."}

        def haversine(lat1, lon1, lat2, lon2):
            # Returns distance in kilometers between two coords.
            R = 6371
            dlat = radians(lat2 - lat1)
            dlon = radians(lon2 - lon1)
            a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))
            return R * c

        results = []
        for biz in self.businesses.values():
            if not biz.get("is_active", False):
                continue

            if zip_code and biz.get("zip_code", "").lower() != zip_code.lower():
                continue
            if city and biz.get("city", "").lower() != city.lower():
                continue
            if state and biz.get("state", "").lower() != state.lower():
                continue

            if latitude is not None and longitude is not None and radius_km is not None:
                dist = haversine(float(latitude), float(longitude),
                                 float(biz.get("latitude", 0.0)),
                                 float(biz.get("longitude", 0.0)))
                if dist > radius_km:
                    continue

            results.append(biz)

        return {"success": True, "data": results}

    def get_business_by_id(self, business_id: str) -> dict:
        """
        Retrieve all details for a single business given its business_id.

        Args:
            business_id (str): The unique identifier for the business.

        Returns:
            dict: {
                "success": True,
                "data": BusinessInfo  # Details for the found business
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, if not found
            }

        Constraints:
            - Returns details for the business regardless of active status.
            - If business_id does not exist, returns an error.
        """
        business = self.businesses.get(business_id)
        if business is None:
            return { "success": False, "error": "Business not found" }
        return { "success": True, "data": business }

    def list_business_reviews(self, business_id: str) -> dict:
        """
        Retrieve all reviews for a given business, including ratings and contents.

        Args:
            business_id (str): The unique identifier of the business.

        Returns:
            dict:
                {"success": True, "data": List[ReviewInfo]}  # All reviews for the business (possibly empty)
            or
                {"success": False, "error": str}             # If business not found

        Constraints:
            - The specified business must exist in the platform.
            - All returned reviews are associated with that business_id.
        """
        if business_id not in self.businesses:
            return {"success": False, "error": "Business does not exist."}

        reviews = [
            review for review in self.reviews.values()
            if review["business_id"] == business_id
        ]

        return {"success": True, "data": reviews}

    def get_business_average_rating(self, business_id: str) -> dict:
        """
        Compute and return the current average overall rating for a given business.
        The rating is dynamically calculated from all reviews that reference the given business_id.

        Args:
            business_id (str): The unique identifier of the business.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "business_id": str,
                    "average_rating": float,  # 0.0 if no reviews found
                    "review_count": int
                }
            }
            Or
            {
                "success": False,
                "error": str  # Reason why average could not be computed (e.g., business not found)
            }

        Constraints:
            - The business_id must reference an existing business.
            - Only ratings from reviews referencing this business_id are included.
            - If there are no reviews, average_rating will be 0.0.
        """
        if business_id not in self.businesses:
            return {"success": False, "error": "Business not found"}
    
        # Get all reviews for the business
        ratings = [
            r["rating"]
            for r in self.reviews.values()
            if r["business_id"] == business_id
        ]
        review_count = len(ratings)
        average_rating = sum(ratings) / review_count if review_count > 0 else 0.0

        return {
            "success": True,
            "data": {
                "business_id": business_id,
                "average_rating": average_rating,
                "review_count": review_count
            }
        }

    def get_top_rated_businesses(
        self,
        category: str = None,
        city: str = None,
        state: str = None,
        zip_code: str = None,
        limit: int = None
    ) -> dict:
        """
        Return businesses sorted by overall_rating (highest first), with optional filters for category and location.

        Args:
            category (str, optional): Only include businesses in this category.
            city (str, optional): Only include businesses in this city.
            state (str, optional): Only include businesses in this state.
            zip_code (str, optional): Only include businesses in this zip code.
            limit (int, optional): Max number of top businesses to return.

        Returns:
            dict: {
                "success": True,
                "data": List[BusinessInfo],  # Sorted, possibly empty.
            }
            or
            {
                "success": False,
                "error": str  # Error reason
            }

        Constraints:
            - Only active businesses (is_active=True) are considered.
            - Location filters are ANDed with category if specified.
            - Sorted by overall_rating (descending), then review_count (descending), then name (ascending).
            - limit, if specified, must be a positive integer.
        """
        # Validate limit
        if limit is not None:
            if not isinstance(limit, int) or limit <= 0:
                return {"success": False, "error": "limit must be a positive integer if provided"}

        # Filter only active businesses
        candidates = [
            b for b in self.businesses.values()
            if b.get("is_active", False)
        ]

        # Apply optional filters
        if category:
            candidates = [
                b for b in candidates
                if category.lower() in [c.lower() for c in b.get("categories", [])]
            ]
        if city:
            candidates = [
                b for b in candidates
                if b.get("city", "").lower() == city.lower()
            ]
        if state:
            candidates = [
                b for b in candidates
                if b.get("state", "").lower() == state.lower()
            ]
        if zip_code:
            candidates = [
                b for b in candidates
                if b.get("zip_code", "") == zip_code
            ]

        # Sort: overall_rating desc, review_count desc, name asc
        candidates.sort(
            key=lambda b: (
                -b.get("overall_rating", 0),
                -b.get("review_count", 0),
                b.get("name", "")
            )
        )

        if limit is not None:
            candidates = candidates[:limit]

        return {
            "success": True,
            "data": candidates
        }

    def get_all_categories(self) -> dict:
        """
        Retrieve the list of all unique categories used among businesses in the environment.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[str]  # Sorted list of unique categories used by any business (may be empty if no businesses)
            }
        Constraints:
            - Considers all businesses, regardless of their active status.
            - If no businesses or no categories, returns empty list.
        """
        categories_set = set()
        for business in self.businesses.values():
            categories_set.update(business.get("categories", []))
        categories_list = sorted(categories_set)
        return { "success": True, "data": categories_list }

    def get_review_by_id(self, review_id: str) -> dict:
        """
        Retrieve details of a review given its unique review_id.

        Args:
            review_id (str): The unique identifier of the review.

        Returns:
            dict:
                - {"success": True, "data": ReviewInfo} if found
                - {"success": False, "error": "Review not found"} if not found

        Constraints:
            - Reviews must reference valid users and businesses, but this method only does a direct lookup.
        """
        review = self.reviews.get(review_id)
        if not review:
            return { "success": False, "error": "Review not found" }
        return { "success": True, "data": review }

    def get_user_reviews(self, user_id: str) -> dict:
        """
        Retrieve all reviews submitted by the specified user.

        Args:
            user_id (str): The user ID for which to return reviews.

        Returns:
            dict: {
                "success": True,
                "data": List[ReviewInfo],
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - user_id must exist in the platform.
            - If user has not submitted any reviews, returned list will be empty.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        reviews = [
            review for review in self.reviews.values()
            if review["user_id"] == user_id
        ]
        return {"success": True, "data": reviews}

    def add_review(
        self,
        business_id: str,
        user_id: str,
        rating: float,
        text: str,
        date: str,
        votes: int = 0
    ) -> dict:
        """
        Add a new review by user for a business, and update business and user aggregates.

        Args:
            business_id (str): The business being reviewed.
            user_id (str): The user writing the review.
            rating (float): The star rating (should be 1-5).
            text (str): Content of the review.
            date (str): Date of submission.
            votes (int, optional): Initial number of votes (default 0).

        Returns:
            dict: {
                "success": True,
                "message": "Review added successfully",
                "review_id": <generated_review_id>
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - business_id must exist and be active.
            - user_id must exist.
            - rating must be float in range 1-5.
            - text must be non-empty.
            - On success, updates business's review_count/overall_rating and user's review_count/average_rating_given.
        """
        # Validate business
        biz = self.businesses.get(business_id)
        if not biz:
            return {"success": False, "error": "Business not found"}
        if not biz["is_active"]:
            return {"success": False, "error": "Business is not active"}

        # Validate user
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User not found"}

        # Validate rating
        try:
            rating = float(rating)
        except ValueError:
            return {"success": False, "error": "Invalid rating value"}
        if rating < 1.0 or rating > 5.0:
            return {"success": False, "error": "Rating must be between 1 and 5"}

        # Validate text
        if not isinstance(text, str) or not text.strip():
            return {"success": False, "error": "Review text must be non-empty"}

        # Generate unique review_id (simple incremental)
        next_id_num = len(self.reviews) + 1
        while True:
            review_id = f"review_{next_id_num}"
            if review_id not in self.reviews:
                break
            next_id_num += 1

        # Create ReviewInfo
        review_info = {
            "review_id": review_id,
            "business_id": business_id,
            "user_id": user_id,
            "rating": rating,
            "text": text,
            "date": date,
            "votes": votes
        }

        # Add to reviews
        self.reviews[review_id] = review_info

        # --- Update business aggregates ---
        # Get all ratings for this business (including the new one)
        ratings = [r["rating"] for r in self.reviews.values() if r["business_id"] == business_id]
        review_count = len(ratings)
        overall_rating = sum(ratings) / review_count if review_count > 0 else 0.0
        # Update business info
        biz["review_count"] = review_count
        biz["overall_rating"] = round(overall_rating, 2)
        self.businesses[business_id] = biz

        # --- Update user aggregates ---
        # Get all ratings provided by this user (including the new one)
        user_ratings = [r["rating"] for r in self.reviews.values() if r["user_id"] == user_id]
        user_review_count = len(user_ratings)
        avg_rating_given = sum(user_ratings) / user_review_count if user_review_count > 0 else 0.0
        user["review_count"] = user_review_count
        user["average_rating_given"] = round(avg_rating_given, 2)
        self.users[user_id] = user

        return {
            "success": True,
            "message": "Review added successfully",
            "review_id": review_id
        }

    def update_business_rating(self, business_id: str) -> dict:
        """
        Recalculate and update the `overall_rating` and `review_count` for a business
        based on its associated reviews.

        Args:
            business_id (str): The unique ID of the business to update.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Business overall_rating updated to X.XX with N reviews."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Business not found"
                    }

        Constraints:
            - If there are zero reviews, overall_rating will be set to 0.0 and review_count to 0.
        """
        if business_id not in self.businesses:
            return { "success": False, "error": "Business not found" }

        # Gather all reviews for this business
        related_reviews = [
            review for review in self.reviews.values()
            if review["business_id"] == business_id
        ]
        review_count = len(related_reviews)
        if review_count > 0:
            total_rating = sum([review["rating"] for review in related_reviews])
            overall_rating = round(total_rating / review_count, 2)
        else:
            overall_rating = 0.0

        # Update in-place
        self.businesses[business_id]["overall_rating"] = overall_rating
        self.businesses[business_id]["review_count"] = review_count

        return {
            "success": True,
            "message": f"Business overall_rating updated to {overall_rating} with {review_count} reviews."
        }

    def add_business(
        self,
        business_id: str,
        name: str,
        categories: list,
        address: str,
        city: str,
        state: str,
        zip_code: str,
        latitude: float,
        longitude: float,
        phone: str,
        is_active: bool = True,
    ) -> dict:
        """
        Adds a new business to the environment with all required fields and metadata.

        Args:
            business_id (str): Unique business ID.
            name (str): Business name.
            categories (list): List of categories.
            address (str): Street address.
            city (str): City where the business is located.
            state (str): State where the business is located.
            zip_code (str): Zip code (required for valid location).
            latitude (float): Latitude of the business.
            longitude (float): Longitude of the business.
            phone (str): Contact phone number.
            is_active (bool): Whether the business is currently active. Defaults to True.

        Returns:
            dict: {
                "success": True,
                "message": "Business added successfully"
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - business_id must be unique.
            - Must provide valid zip_code and location data.
            - Name must not be empty.
        """
        # Validate business_id uniqueness
        if business_id in self.businesses:
            return {"success": False, "error": "Business ID already exists"}
        # Validate required fields
        if not all([business_id, name, categories, address, city, state, zip_code, phone]):
            return {"success": False, "error": "Missing required business fields"}
        if not isinstance(categories, list) or not categories:
            return {"success": False, "error": "Categories must be a non-empty list"}
        if not isinstance(latitude, float) or not isinstance(longitude, float):
            return {"success": False, "error": "Latitude and longitude must be floats"}
        if not isinstance(zip_code, str) or not zip_code.strip():
            return {"success": False, "error": "Invalid zip_code"}
        if not isinstance(is_active, bool):
            return {"success": False, "error": "is_active must be boolean"}

        # Create business info (with derived fields)
        business_info = {
            "business_id": business_id,
            "name": name,
            "categories": categories,
            "address": address,
            "city": city,
            "state": state,
            "zip_code": zip_code,
            "latitude": latitude,
            "longitude": longitude,
            "phone": phone,
            "overall_rating": 0.0,
            "review_count": 0,
            "is_active": is_active,
        }

        self.businesses[business_id] = business_info

        return {"success": True, "message": "Business added successfully"}

    def set_business_active_status(self, business_id: str, is_active: bool) -> dict:
        """
        Toggle or update the `is_active` status of a business.

        Args:
            business_id (str): The unique identifier of the business.
            is_active (bool): The desired active status (True = open/active, False = closed/inactive).

        Returns:
            dict: {
                "success": True,
                "message": "Business status updated to active/inactive."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., business not found.
            }

        Constraints:
            - The business with the given ID must exist.
            - Sets the active status regardless of prior value (idempotent).
        """
        business = self.businesses.get(business_id)
        if business is None:
            return { "success": False, "error": "Business not found" }
        business["is_active"] = is_active
        status_str = "active" if is_active else "inactive"
        return { "success": True, "message": f"Business status updated to {status_str}." }

    def edit_business_info(self, business_id: str, update_fields: dict) -> dict:
        """
        Update metadata for an existing business (e.g., categories, address, contact info).

        Args:
            business_id (str): Unique ID for the business to update.
            update_fields (dict): Dictionary of fields to update. Valid fields include:
                - name (str)
                - categories (List[str])
                - address (str)
                - city (str)
                - state (str)
                - zip_code (str)
                - latitude (float)
                - longitude (float)
                - phone (str)

        Returns:
            dict:
                - {"success": True, "message": "Business info updated successfully"} if update succeeds
                - {"success": False, "error": "<reason>"} on failure

        Constraints:
            - business_id must exist.
            - Fields overall_rating, review_count, is_active, business_id are not directly editable via this method.
            - Cannot add new/unknown attributes.
            - zip_code must remain non-empty if changed.
        """
        # Check if business exists
        if business_id not in self.businesses:
            return {"success": False, "error": "Business not found"}

        business = self.businesses[business_id]
        editable_fields = {
            "name", "categories", "address", "city", "state",
            "zip_code", "latitude", "longitude", "phone"
        }
        protected_fields = {"overall_rating", "review_count", "is_active", "business_id"}

        for key in update_fields:
            if key in protected_fields:
                return {"success": False, "error": f"Field '{key}' cannot be updated directly"}
            if key not in editable_fields:
                return {"success": False, "error": f"Unknown or unsupported field: '{key}'"}

        # Validate critical fields if included
        if "zip_code" in update_fields and (not update_fields["zip_code"] or not isinstance(update_fields["zip_code"], str)):
            return {"success": False, "error": "zip_code must be a non-empty string"}

        # Update fields
        for key, value in update_fields.items():
            business[key] = value

        self.businesses[business_id] = business
        return {"success": True, "message": "Business info updated successfully"}

    def delete_review(self, review_id: str) -> dict:
        """
        Remove a review by its review_id from the system and update the associated business's
        and user's review statistics (review_count, overall_rating, average_rating_given).

        Args:
            review_id (str): The ID of the review to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Review deleted and business/user statistics updated"
            }
            or
            {
                "success": False,
                "error": <error_message>
            }

        Constraints:
            - Review must exist.
            - Business and user referenced by review must exist.
            - After deletion, business and user statistics must be recalculated to reflect the change.
        """
        review = self.reviews.get(review_id)
        if review is None:
            return { "success": False, "error": "Review not found" }

        business_id = review.get("business_id")
        user_id = review.get("user_id")

        business = self.businesses.get(business_id)
        user = self.users.get(user_id)

        if business is None:
            return { "success": False, "error": "Associated business not found" }
        if user is None:
            return { "success": False, "error": "Associated user not found" }

        # Delete the review
        del self.reviews[review_id]

        # Update business review_count and overall_rating
        business_review_ids = [
            rid for rid, r in self.reviews.items() if r["business_id"] == business_id
        ]
        business["review_count"] = len(business_review_ids)
        if business["review_count"] > 0:
            # Compute new average
            total_rating = sum(self.reviews[rid]["rating"] for rid in business_review_ids)
            business["overall_rating"] = round(total_rating / business["review_count"], 2)
        else:
            business["overall_rating"] = 0.0

        # Update user review_count and average_rating_given
        user_review_ids = [
            rid for rid, r in self.reviews.items() if r["user_id"] == user_id
        ]
        user["review_count"] = len(user_review_ids)
        if user["review_count"] > 0:
            total_user_rating = sum(self.reviews[rid]["rating"] for rid in user_review_ids)
            user["average_rating_given"] = round(total_user_rating / user["review_count"], 2)
        else:
            user["average_rating_given"] = 0.0

        return { "success": True, "message": "Review deleted and business/user statistics updated" }


class YelpEnvironment(BaseEnv):
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

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def get_user_by_name(self, **kwargs):
        return self._call_inner_tool('get_user_by_name', kwargs)

    def search_businesses(self, **kwargs):
        return self._call_inner_tool('search_businesses', kwargs)

    def filter_businesses_by_category(self, **kwargs):
        return self._call_inner_tool('filter_businesses_by_category', kwargs)

    def filter_businesses_by_location(self, **kwargs):
        return self._call_inner_tool('filter_businesses_by_location', kwargs)

    def get_business_by_id(self, **kwargs):
        return self._call_inner_tool('get_business_by_id', kwargs)

    def list_business_reviews(self, **kwargs):
        return self._call_inner_tool('list_business_reviews', kwargs)

    def get_business_average_rating(self, **kwargs):
        return self._call_inner_tool('get_business_average_rating', kwargs)

    def get_top_rated_businesses(self, **kwargs):
        return self._call_inner_tool('get_top_rated_businesses', kwargs)

    def get_all_categories(self, **kwargs):
        return self._call_inner_tool('get_all_categories', kwargs)

    def get_review_by_id(self, **kwargs):
        return self._call_inner_tool('get_review_by_id', kwargs)

    def get_user_reviews(self, **kwargs):
        return self._call_inner_tool('get_user_reviews', kwargs)

    def add_review(self, **kwargs):
        return self._call_inner_tool('add_review', kwargs)

    def update_business_rating(self, **kwargs):
        return self._call_inner_tool('update_business_rating', kwargs)

    def add_business(self, **kwargs):
        return self._call_inner_tool('add_business', kwargs)

    def set_business_active_status(self, **kwargs):
        return self._call_inner_tool('set_business_active_status', kwargs)

    def edit_business_info(self, **kwargs):
        return self._call_inner_tool('edit_business_info', kwargs)

    def delete_review(self, **kwargs):
        return self._call_inner_tool('delete_review', kwargs)
