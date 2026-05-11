# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



class AppInfo(TypedDict, total=False):
    app_id: str
    name: str
    developer_id: str
    description: str
    category: str
    icon_url: str
    release_date: str  # ISO date string
    version: str
    countries_available: List[str]
    # 'etc.' fields can be extended as needed

class ReviewInfo(TypedDict):
    review_id: str
    app_id: str
    author_id: str
    stars: int
    content: str
    timestamp: str  # ISO date string or float epoch time
    helpfulness_score: float
    country: str
    language: str
    status: str  # e.g., 'visible', 'hidden', 'pending'

class SimilarAppRelationshipInfo(TypedDict):
    source_app_id: str
    target_app_id: str
    similarity_score: float

class DeveloperInfo(TypedDict):
    developer_id: str
    name: str
    organization: str
    contact_info: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment structure for App Store metadata and reviews.
        """

        # Apps: {app_id: AppInfo}
        # entity: App (attributes: app_id, name, developer_id, description, category, icon_url, release_date, version, countries_available, etc.)
        self.apps: Dict[str, AppInfo] = {}

        # Reviews: {review_id: ReviewInfo}
        # entity: Review (attributes: review_id, app_id, author_id, stars, content, timestamp, helpfulness_score, country, language, status)
        self.reviews: Dict[str, ReviewInfo] = {}

        # Similar App Relationships: List[SimilarAppRelationshipInfo]
        # entity: SimilarAppRelationship (attributes: source_app_id, target_app_id, similarity_score)
        self.similar_app_relationships: List[SimilarAppRelationshipInfo] = []

        # Developers: {developer_id: DeveloperInfo}
        # entity: Developer (attributes: developer_id, name, organization, contact_info)
        self.developers: Dict[str, DeveloperInfo] = {}

        # Constraints:
        # - Each review must be associated with exactly one app (via app_id).
        # - Review visibility or retrieval may be restricted by country or language.
        # - Similar app relationships should link existing apps only.
        # - Helpfulness scores must be calculable (e.g., derived from user feedback or votes).
        # - An app can appear in multiple countries; certain metadata or reviews may be country-specific.

    def get_app_by_id(self, app_id: str) -> dict:
        """
        Retrieve metadata for a given app by its app_id.

        Args:
            app_id (str): The unique app identifier.

        Returns:
            dict: 
                - On success: {
                      "success": True,
                      "data": AppInfo  # The metadata dict for this app
                  }
                - On failure (app not found): {
                      "success": False,
                      "error": "App ID not found"
                  }
        Constraints:
            - The given app_id must exist in the app store database.
        """
        app_info = self.apps.get(app_id)
        if app_info is None:
            return {
                "success": False,
                "error": "App ID not found"
            }
        return {
            "success": True,
            "data": app_info
        }

    def get_reviews_by_app_id(self, app_id: str) -> dict:
        """
        Retrieve all reviews associated with a specific app_id.
    
        Args:
            app_id (str): The unique identifier for the app.
    
        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": List[ReviewInfo]  # All reviews for the app (may be empty)
                    }
                - On failure:
                    {
                        "success": False,
                        "error": str  # "App does not exist"
                    }
    
        Constraints:
            - The app_id must exist in the database.
            - Returns all reviews for the app regardless of visibility status, country, or language.
        """
        if app_id not in self.apps:
            return { "success": False, "error": "App does not exist" }
    
        reviews = [
            review for review in self.reviews.values()
            if review["app_id"] == app_id
        ]
        return { "success": True, "data": reviews }

    def get_reviews_by_app_and_country(self, app_id: str, country: str) -> dict:
        """
        Retrieve visible reviews for the given app_id, filtered by the specified country.

        Args:
            app_id (str): The unique identifier of the app whose reviews should be returned.
            country (str): The country code to filter reviews (e.g., 'US', 'CN').

        Returns:
            dict: {
                "success": True,
                "data": List[ReviewInfo]  # Only visible reviews for that app and country
            }
            or
            {
                "success": False,
                "error": str  # App does not exist, etc.
            }

        Constraints:
            - App must exist.
            - Only reviews with status 'visible' are returned.
        """
        if app_id not in self.apps:
            return {"success": False, "error": "App does not exist"}

        data = [
            r for r in self.reviews.values()
            if r["app_id"] == app_id and r["country"] == country and r.get("status", "visible") == "visible"
        ]
        return {"success": True, "data": data}

    def get_reviews_by_app_country_sorted_helpfulness(self, app_id: str, country: str) -> dict:
        """
        Retrieve all 'visible' reviews for a specified app_id and country,
        sorted by helpfulness_score in descending order.

        Args:
            app_id (str): The unique identifier for the app.
            country (str): The country code to filter reviews by.

        Returns:
            dict: {
                "success": True,
                "data": List[ReviewInfo],  # can be empty if no matching reviews
            }
            or
            {
                "success": False,
                "error": str  # if app_id not found or other error
            }

        Constraints:
            - app_id must exist in the database.
            - Only reviews with status "visible" are included.
        """
        if app_id not in self.apps:
            return { "success": False, "error": "App ID not found" }
    
        filtered_reviews = [
            review for review in self.reviews.values()
            if (
                review["app_id"] == app_id and
                review["country"] == country and
                review["status"] == "visible"
            )
        ]
        # Sort in-place by helpfulness_score descending
        filtered_reviews.sort(key=lambda r: r.get("helpfulness_score", 0), reverse=True)
        return {
            "success": True,
            "data": filtered_reviews
        }

    def get_review_by_id(self, review_id: str) -> dict:
        """
        Retrieve a specific review by its unique review_id.

        Args:
            review_id (str): Unique identifier of the review to fetch.

        Returns:
            dict: 
                On success:
                    { "success": True, "data": ReviewInfo }
                On failure:
                    { "success": False, "error": "Review not found" }

        Constraints:
            - The review_id must exist in the database.
        """
        review = self.reviews.get(review_id)
        if review is None:
            return { "success": False, "error": "Review not found" }
        else:
            return { "success": True, "data": review }

    def get_app_similar_apps(self, source_app_id: str) -> dict:
        """
        Retrieve similar (recommended/related) apps for a given source_app_id.

        Args:
            source_app_id (str): The app_id for which to fetch similar apps.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": List[{"app": AppInfo, "similarity_score": float}]
                    }
                - On failure:
                    {
                        "success": False,
                        "error": str  # reason (e.g., app not found)
                    }
    
        Constraints:
            - source_app_id must refer to an existing app.
            - Similar app relationships should link existing apps only (but double-check target existence).
        """
        if source_app_id not in self.apps:
            return {"success": False, "error": "Source app does not exist."}

        similar_list = []
        for rel in self.similar_app_relationships:
            if rel["source_app_id"] == source_app_id:
                target_id = rel["target_app_id"]
                # Double-check that the target app exists (should always be true)
                if target_id in self.apps:
                    similar_list.append({
                        "app": self.apps[target_id],
                        "similarity_score": rel["similarity_score"]
                    })
                # If target does not exist, we skip silently for robustness

        return {"success": True, "data": similar_list}

    def get_developer_by_id(self, developer_id: str) -> dict:
        """
        Retrieve information about a developer given their developer_id.

        Args:
            developer_id (str): Unique identifier for the developer.

        Returns:
            dict:
                On success: { "success": True, "data": DeveloperInfo }
                On failure: { "success": False, "error": "Developer not found" }
        Constraints:
            - The developer_id must correspond to an existing developer in the database.
        """
        dev = self.developers.get(developer_id)
        if dev is None:
            return { "success": False, "error": "Developer not found" }
        return { "success": True, "data": dev }

    def list_apps_by_developer(self, developer_id: str) -> dict:
        """
        List all applications published by the given developer.

        Args:
            developer_id (str): Unique identifier for the developer.

        Returns:
            dict: 
                - success: True, data: List[AppInfo] where each app's developer_id matches.
                - success: False, error: if the developer_id does not exist.
    
        Constraints:
            - The developer_id must exist in the developers dictionary.
            - If the developer exists but has published no apps, data will be empty list.
        """
        if developer_id not in self.developers:
            return { "success": False, "error": "Developer does not exist" }

        apps = [
            app_info for app_info in self.apps.values()
            if app_info.get("developer_id") == developer_id
        ]
        return { "success": True, "data": apps }

    def get_review_helpfulness_score(self, review_id: str) -> dict:
        """
        Retrieve the helpfulness score of a specific review.

        Args:
            review_id (str): The unique ID of the review.

        Returns:
            dict: {
                'success': True,
                'data': float  # The helpfulness score of the review
            }
            or
            {
                'success': False,
                'error': str  # Error message, e.g., review not found
            }

        Constraints:
            - Review must exist in the database.
        """
        review = self.reviews.get(review_id)
        if review is None:
            return { "success": False, "error": "Review not found" }

        return { "success": True, "data": review["helpfulness_score"] }

    def list_available_countries_for_app(self, app_id: str) -> dict:
        """
        List all countries in which a specific app is available.

        Args:
            app_id (str): The unique identifier for the app.

        Returns:
            dict:
                - On success:
                    {"success": True, "data": List[str]}  # list of country codes or names
                - On error:
                    {"success": False, "error": "App not found"}
        Constraints:
            - The specified app_id must exist in the system.
        """
        app = self.apps.get(app_id)
        if not app:
            return {"success": False, "error": "App not found"}
        countries = app.get("countries_available", [])
        return {"success": True, "data": countries}

    def hide_review(self, review_id: str) -> dict:
        """
        Set the status of a review to 'hidden' for visibility management.

        Args:
            review_id (str): The unique ID of the review to hide.

        Returns:
            dict:
                On success:
                    { 'success': True, 'message': 'Review <review_id> hidden.' }
                On failure:
                    { 'success': False, 'error': 'Review not found.' }

        Constraints:
            - If the review does not exist, returns an error.
            - If the review is already hidden, treats as success (idempotent).
            - Only modifies the 'status' field of the review.
        """
        if review_id not in self.reviews:
            return { "success": False, "error": "Review not found." }

        review = self.reviews[review_id]
        if review.get("status") == "hidden":
            return { "success": True, "message": f"Review {review_id} was already hidden." }

        review["status"] = "hidden"
        self.reviews[review_id] = review
        return { "success": True, "message": f"Review {review_id} hidden." }

    def unhide_review(self, review_id: str) -> dict:
        """
        Set the status of a review with the given review_id back to "visible".

        Args:
            review_id (str): The ID of the review whose status is to be set to "visible".

        Returns:
            dict: On success:
                {
                    "success": True,
                    "message": "Review set to visible."
                }
                On error (e.g., review_id not found):
                {
                    "success": False,
                    "error": "Review not found"
                }

        Constraints:
            - The review_id must exist in the database.
            - No side effect other than updating the status field for the matched review.
        """
        if review_id not in self.reviews:
            return { "success": False, "error": "Review not found" }

        self.reviews[review_id]['status'] = 'visible'
        return { "success": True, "message": "Review set to visible." }

    def add_review(
        self,
        review_id: str,
        app_id: str,
        author_id: str,
        stars: int,
        content: str,
        timestamp: str,
        country: str,
        language: str,
        helpfulness_score: float = 0.0,
        status: str = "visible"
    ) -> dict:
        """
        Add a new review for an app, validating existence of app, country availability, 
        and uniqueness constraints.

        Args:
            review_id (str): Unique identifier for the review.
            app_id (str): ID of the app being reviewed.
            author_id (str): Reviewer user ID.
            stars (int): Star rating (1-5).
            content (str): Review text.
            timestamp (str): Creation time (ISO format).
            country (str): Country of the review.
            language (str): Language of the review.
            helpfulness_score (float, optional): Helpfulness score. Defaults to 0.0.
            status (str, optional): Review status ('visible', etc). Defaults to 'visible'.

        Returns:
            dict: Success message or error:
                { "success": True, "message": "Review added successfully" }
                or
                { "success": False, "error": "<reason>" }

        Constraints:
            - Review must be for an existing app_id.
            - Country must be in the app's countries_available list.
            - review_id must be unique.
            - stars must be from 1 to 5 (inclusive).
        """
        # Check if review_id is unique
        if review_id in self.reviews:
            return {"success": False, "error": "Review ID already exists"}

        # Check if app exists
        app = self.apps.get(app_id)
        if not app:
            return {"success": False, "error": "App ID does not exist"}

        # Check country
        countries = app.get('countries_available', [])
        if country not in countries:
            return {"success": False, "error": "Review country not available for this app"}

        # Stars validation
        if not (1 <= stars <= 5):
            return {"success": False, "error": "Stars must be between 1 and 5"}

        # Assemble the review info
        review_info = {
            "review_id": review_id,
            "app_id": app_id,
            "author_id": author_id,
            "stars": stars,
            "content": content,
            "timestamp": timestamp,
            "helpfulness_score": float(helpfulness_score),
            "country": country,
            "language": language,
            "status": status,
        }

        self.reviews[review_id] = review_info
        return {"success": True, "message": "Review added successfully"}

    def update_review_helpfulness_score(self, review_id: str, helpfulness_score: float) -> dict:
        """
        Update the helpfulness_score of a specified review.

        Args:
            review_id (str): The unique identifier of the review to update.
            helpfulness_score (float): The new helpfulness score to set.
    
        Returns:
            dict: {
                "success": True,
                "message": "Review helpfulness_score updated."
            } 
            or 
            {
                "success": False,
                "error": "reason"
            }
    
        Constraints:
            - The review must exist.
            - The score should be a float (generally >= 0.0).
        """
        if review_id not in self.reviews:
            return {"success": False, "error": "Review does not exist."}
    
        try:
            score_val = float(helpfulness_score)
        except (TypeError, ValueError):
            return {"success": False, "error": "Invalid helpfulness_score value."}
        if score_val < 0:
            return {"success": False, "error": "helpfulness_score must be non-negative."}

        self.reviews[review_id]["helpfulness_score"] = score_val
        return {"success": True, "message": "Review helpfulness_score updated."}

    def add_similar_app_relationship(
        self,
        source_app_id: str,
        target_app_id: str,
        similarity_score: float
    ) -> dict:
        """
        Create a new similar app relationship between two valid app_ids.

        Args:
            source_app_id (str): The app recommending another app.
            target_app_id (str): The app being recommended as similar.
            similarity_score (float): The degree of similarity (should be between 0 and 1, but not strictly enforced).

        Returns:
            dict: {
                "success": True,
                "message": "Similar app relationship added between <source_app_id> and <target_app_id>."
            }
            or
            {
                "success": False,
                "error": <reason string>
            }

        Constraints:
            - Both app ids must exist in the database.
            - No duplicate exact (source, target) relationship is allowed.
        """
        if source_app_id not in self.apps:
            return { "success": False, "error": f"Source app_id '{source_app_id}' does not exist." }
        if target_app_id not in self.apps:
            return { "success": False, "error": f"Target app_id '{target_app_id}' does not exist." }

        # Prevent duplicate relationships
        for rel in self.similar_app_relationships:
            if rel['source_app_id'] == source_app_id and rel['target_app_id'] == target_app_id:
                return {
                    "success": False,
                    "error": f"Relationship between '{source_app_id}' and '{target_app_id}' already exists."
                }

        new_relationship: SimilarAppRelationshipInfo = {
            "source_app_id": source_app_id,
            "target_app_id": target_app_id,
            "similarity_score": similarity_score
        }
        self.similar_app_relationships.append(new_relationship)

        return {
            "success": True,
            "message": f"Similar app relationship added between '{source_app_id}' and '{target_app_id}'."
        }

    def remove_similar_app_relationship(self, source_app_id: str, target_app_id: str) -> dict:
        """
        Remove all similarity relationships between source_app_id and target_app_id.

        Args:
            source_app_id (str): The app_id of the source app.
            target_app_id (str): The app_id of the target app.

        Returns:
            dict: 
                - {"success": True, "message": "..."} on success.
                - {"success": False, "error": "..."} if the relationship did not exist.

        Constraints:
            - If multiple such relationships are present, all are removed.
            - Relationship must exist to be removed; otherwise, returns error.
        """
        before_count = len(self.similar_app_relationships)
        # Filter out all relationships between source and target
        self.similar_app_relationships = [
            rel for rel in self.similar_app_relationships
            if not (rel["source_app_id"] == source_app_id and rel["target_app_id"] == target_app_id)
        ]
        after_count = len(self.similar_app_relationships)
        removed = before_count - after_count

        if removed == 0:
            return {"success": False, "error": "No such similar app relationship found"}
        else:
            return {
                "success": True,
                "message": f"Removed {removed} similar app relationship(s) between '{source_app_id}' and '{target_app_id}'."
            }

    def update_app_metadata(self, app_id: str, updated_fields: dict) -> dict:
        """
        Edit the metadata of an existing app.

        Args:
            app_id (str): The ID of the app whose metadata is to be updated.
            updated_fields (dict): A dictionary of {field: value} pairs to update in the app's metadata.
                Allowed keys include any AppInfo fields such as description, category, icon_url, etc.

        Returns:
            dict: 
                - On success: { "success": True, "message": "App metadata updated successfully." }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - The app must exist.
            - Only existing AppInfo fields are updated; unknown fields are ignored.
        """
        app = self.apps.get(app_id)
        if app is None:
            return { "success": False, "error": "App not found." }

        allowed_fields = set(app.keys())
        updated_any = False
        for key, value in updated_fields.items():
            if key in allowed_fields:
                app[key] = value
                updated_any = True
            # Ignore unknown fields silently

        # Even if nothing changed, we treat as success (no-op)
        return { "success": True, "message": "App metadata updated successfully." }

    def add_app_to_country(self, app_id: str, country_code: str) -> dict:
        """
        Add the specified ISO country code to the app's countries_available list.

        Args:
            app_id (str): Unique identifier for the app.
            country_code (str): ISO country code to add to the app's availability.

        Returns:
            dict:
                - {"success": True, "message": str} on success (including if already present).
                - {"success": False, "error": str} on failure (e.g., app_id not found).

        Constraints:
            - app_id must exist in self.apps.
            - countries_available list must contain at most one of each country code.

        Notes:
            - If app is already available in the given country, operation is a no-op (idempotent).
            - If countries_available attribute is missing, it will be created.
        """
        app = self.apps.get(app_id)
        if not app:
            return {"success": False, "error": "App ID not found"}

        # Defensive: ensure countries_available exists and is a list
        if "countries_available" not in app or not isinstance(app["countries_available"], list):
            app["countries_available"] = []

        if country_code in app["countries_available"]:
            return {
                "success": True,
                "message": f"App is already available in country: {country_code}"
            }

        app["countries_available"].append(country_code)
        self.apps[app_id] = app  # Save back in case of non-direct reference

        return {
            "success": True,
            "message": f"Country {country_code} added to countries_available list for app."
        }


class AppStoreMetadataReviewDatabase(BaseEnv):
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

    def get_app_by_id(self, **kwargs):
        return self._call_inner_tool('get_app_by_id', kwargs)

    def get_reviews_by_app_id(self, **kwargs):
        return self._call_inner_tool('get_reviews_by_app_id', kwargs)

    def get_reviews_by_app_and_country(self, **kwargs):
        return self._call_inner_tool('get_reviews_by_app_and_country', kwargs)

    def get_reviews_by_app_country_sorted_helpfulness(self, **kwargs):
        return self._call_inner_tool('get_reviews_by_app_country_sorted_helpfulness', kwargs)

    def get_review_by_id(self, **kwargs):
        return self._call_inner_tool('get_review_by_id', kwargs)

    def get_app_similar_apps(self, **kwargs):
        return self._call_inner_tool('get_app_similar_apps', kwargs)

    def get_developer_by_id(self, **kwargs):
        return self._call_inner_tool('get_developer_by_id', kwargs)

    def list_apps_by_developer(self, **kwargs):
        return self._call_inner_tool('list_apps_by_developer', kwargs)

    def get_review_helpfulness_score(self, **kwargs):
        return self._call_inner_tool('get_review_helpfulness_score', kwargs)

    def list_available_countries_for_app(self, **kwargs):
        return self._call_inner_tool('list_available_countries_for_app', kwargs)

    def hide_review(self, **kwargs):
        return self._call_inner_tool('hide_review', kwargs)

    def unhide_review(self, **kwargs):
        return self._call_inner_tool('unhide_review', kwargs)

    def add_review(self, **kwargs):
        return self._call_inner_tool('add_review', kwargs)

    def update_review_helpfulness_score(self, **kwargs):
        return self._call_inner_tool('update_review_helpfulness_score', kwargs)

    def add_similar_app_relationship(self, **kwargs):
        return self._call_inner_tool('add_similar_app_relationship', kwargs)

    def remove_similar_app_relationship(self, **kwargs):
        return self._call_inner_tool('remove_similar_app_relationship', kwargs)

    def update_app_metadata(self, **kwargs):
        return self._call_inner_tool('update_app_metadata', kwargs)

    def add_app_to_country(self, **kwargs):
        return self._call_inner_tool('add_app_to_country', kwargs)

