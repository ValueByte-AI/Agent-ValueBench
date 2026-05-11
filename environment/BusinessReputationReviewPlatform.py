# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, Optional, TypedDict



class BusinessInfo(TypedDict):
    business_id: str
    name: str
    industry: str
    contact_info: str

class BusinessUnitInfo(TypedDict):
    unit_id: str
    business_id: str  # references parent Business
    name: str
    address: str
    web_link: str
    trust_score: float
    star_rating: float

class ReviewInfo(TypedDict):
    review_id: str
    unit_id: str  # references BusinessUnit
    customer_id: str  # references Customer
    rating: float
    review_text: str
    timestamp: str

class CustomerInfo(TypedDict, total=False):
    customer_id: str
    name: Optional[str]  # Optional/anonymous allowed
    profile_info: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Businesses: {business_id: BusinessInfo}
        self.businesses: Dict[str, BusinessInfo] = {}

        # Business Units: {unit_id: BusinessUnitInfo}
        self.business_units: Dict[str, BusinessUnitInfo] = {}

        # Reviews: {review_id: ReviewInfo}
        self.reviews: Dict[str, ReviewInfo] = {}

        # Customers: {customer_id: CustomerInfo}
        self.customers: Dict[str, CustomerInfo] = {}

        # Constraints:
        # - Trust score and star rating for business units must be periodically recomputed from reviews.
        # - Each business unit must have a valid parent business_id found in self.businesses.
        # - web_link for business unit must be unique and valid (well-formed URL).
        # - Each review must reference one business unit and one customer.
        # - Only verified customers may leave reviews (if account status verification is implemented).

    def get_business_unit_by_id(self, unit_id: str) -> dict:
        """
        Retrieve the full metadata/details for a business unit given its unique unit ID.

        Args:
            unit_id (str): Unique identifier of the business unit.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": BusinessUnitInfo  # All info fields for the business unit
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Business unit not found"
                    }
        """
        business_unit = self.business_units.get(unit_id)
        if business_unit is None:
            return { "success": False, "error": "Business unit not found" }
        return { "success": True, "data": business_unit }

    def get_business_unit_by_name(self, name: str) -> dict:
        """
        Find a business unit by its name and return its info (trust score, star rating, web link, etc.).

        Args:
            name (str): The name of the business unit to search for (case-sensitive).

        Returns:
            dict:
                - On success: { "success": True, "data": BusinessUnitInfo }
                - On failure: { "success": False, "error": "Business unit not found" }

        Notes:
            - If multiple business units have the same name, returns the first match encountered.
            - Comparison is case-sensitive.
        """
        for unit_info in self.business_units.values():
            if unit_info["name"] == name:
                return { "success": True, "data": unit_info }
        return { "success": False, "error": "Business unit not found" }

    def get_business_units_by_business(self, business_id: str) -> dict:
        """
        List all business units belonging to a given business by business_id.

        Args:
            business_id (str): Identifier of the parent business.

        Returns:
            dict: {
                "success": True,
                "data": List[BusinessUnitInfo],  # may be empty if no units found
            }
            or
            {
                "success": False,
                "error": str  # error description, e.g., if business_id is invalid
            }

        Constraints:
            - The specified business_id must exist in the platform.
        """
        if business_id not in self.businesses:
            return {"success": False, "error": "Business ID does not exist"}

        business_units = [
            unit_info for unit_info in self.business_units.values()
            if unit_info["business_id"] == business_id
        ]

        return {"success": True, "data": business_units}

    def get_trust_score_and_rating_for_unit(self, unit_id: str) -> dict:
        """
        Retrieve the trust score and star rating for a specific business unit.

        Args:
            unit_id (str): The unique identifier of the business unit.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": {
                            "trust_score": float,
                            "star_rating": float
                        }
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # "Business unit not found"
                    }
        Constraints:
            - unit_id must exist in the platform.
            - Returns only trust_score and star_rating fields.
        """
        unit = self.business_units.get(unit_id)
        if not unit:
            return { "success": False, "error": "Business unit not found" }

        return {
            "success": True,
            "data": {
                "trust_score": unit["trust_score"],
                "star_rating": unit["star_rating"]
            }
        }

    def get_web_link_for_unit(self, unit_id: str) -> dict:
        """
        Retrieve the web link (URL) for the specified business unit.

        Args:
            unit_id (str): The unique identifier of the business unit.

        Returns:
            dict:
                - On success: { "success": True, "data": str }  # the web link (URL)
                - On failure: { "success": False, "error": str }  # error message

        Constraints:
            - The business unit with the given unit_id must exist.
        """
        unit = self.business_units.get(unit_id)
        if not unit:
            return { "success": False, "error": "Business unit not found" }
        return { "success": True, "data": unit["web_link"] }

    def get_reviews_for_unit(self, unit_id: str) -> dict:
        """
        List all reviews associated with a specific business unit.

        Args:
            unit_id (str): The unique identifier of the business unit.

        Returns:
            dict: {
                "success": True,
                "data": List[ReviewInfo]  # list of matching reviews (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # e.g., 'Business unit does not exist'
            }

        Constraints:
            - The specified business unit (unit_id) must exist.
        """
        if unit_id not in self.business_units:
            return { "success": False, "error": "Business unit does not exist" }

        reviews = [
            review for review in self.reviews.values()
            if review["unit_id"] == unit_id
        ]

        return { "success": True, "data": reviews }

    def get_review_by_id(self, review_id: str) -> dict:
        """
        Fetch details of a single review by its review_id.

        Args:
            review_id (str): The unique identifier of the review.

        Returns:
            dict: 
                On success:
                    {"success": True, "data": ReviewInfo}
                On failure:
                    {"success": False, "error": "Review not found"}
        Constraints:
            - The review_id must exist in the system.
        """
        review = self.reviews.get(review_id)
        if not review:
            return {"success": False, "error": "Review not found"}
        return {"success": True, "data": review}

    def get_business_by_id(self, business_id: str) -> dict:
        """
        Retrieve business details (name, industry, contact) by business_id.

        Args:
            business_id (str): The identifier of the business.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": BusinessInfo
                    }
                If not found:
                    {
                        "success": False,
                        "error": "Business not found"
                    }
        """
        business = self.businesses.get(business_id)
        if business is None:
            return { "success": False, "error": "Business not found" }
        return { "success": True, "data": business }

    def get_customer_by_id(self, customer_id: str) -> dict:
        """
        Retrieve information about a customer given their customer_id.

        Args:
            customer_id (str): The unique identifier of the customer.

        Returns:
            dict:
                - On success: { "success": True, "data": CustomerInfo }
                - On failure: { "success": False, "error": "Customer not found" }

        Constraints:
            - customer_id must be present in self.customers.
            - CustomerInfo's 'name' field may be omitted for anonymity.
        """
        customer = self.customers.get(customer_id)
        if customer is not None:
            return { "success": True, "data": customer }
        else:
            return { "success": False, "error": "Customer not found" }

    def list_all_businesses(self) -> dict:
        """
        List all registered businesses on the platform.

        Returns:
            dict: {
                "success": True,
                "data": List[BusinessInfo]  # List of business info dictionaries. May be empty if no businesses registered.
            }
        """
        businesses_list = list(self.businesses.values())
        return {
            "success": True,
            "data": businesses_list
        }

    def list_all_business_units(self) -> dict:
        """
        List all business units currently on the platform.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[BusinessUnitInfo],  # All business units (may be empty)
            }
        Constraints:
            - No constraints; this is a simple read.
        """
        units = list(self.business_units.values())
        return { "success": True, "data": units }

    def recompute_reputation_metrics_for_unit(self, unit_id: str) -> dict:
        """
        Recalculate the trust score and star rating for the specified business unit
        from all currently associated reviews. Updates the fields in the business unit.

        Args:
            unit_id (str): The unique identifier for the business unit.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Reputation metrics recomputed for business unit <unit_id>."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Business unit not found."
                    }

        Constraints:
            - Fails if the specified business unit does not exist.
            - Sets trust_score and star_rating to 0.0 if there are no reviews.
        """
        # Check business unit exists
        if unit_id not in self.business_units:
            return { "success": False, "error": "Business unit not found." }

        # Collect all ratings from reviews of this unit
        ratings = [
            review["rating"]
            for review in self.reviews.values()
            if review["unit_id"] == unit_id
        ]

        if ratings:
            average_rating = sum(ratings) / len(ratings)
        else:
            average_rating = 0.0

        # Update both trust_score and star_rating to the computed average
        self.business_units[unit_id]["trust_score"] = average_rating
        self.business_units[unit_id]["star_rating"] = average_rating

        return {
            "success": True,
            "message": f"Reputation metrics recomputed for business unit {unit_id}."
        }

    def add_review(
        self,
        review_id: str,
        unit_id: str,
        customer_id: str,
        rating: float,
        review_text: str,
        timestamp: str
    ) -> dict:
        """
        Add a new review for a business unit.

        Args:
            review_id (str): Desired unique review ID.
            unit_id (str): ID of the business unit being reviewed.
            customer_id (str): Customer ID of the reviewer.
            rating (float): Star rating (typically 1-5 float).
            review_text (str): Text/body of the review.
            timestamp (str): Timestamp of review (ISO8601 or similar).

        Returns:
            dict: {
                "success": True,
                "message": "Review added"
            } on success, or
            {
                "success": False,
                "error": <reason>
            } on failure.

        Constraints:
            - Each (unit_id, customer_id) may have only one review.
            - review_id must not already exist.
            - unit_id must exist.
            - customer_id must exist.
            - Optional: only verified customers may review (if verification is implemented).
            - Triggers recomputation of reputation metrics for the unit after addition.
        """
        # Check uniqueness of review_id
        if review_id in self.reviews:
            return {"success": False, "error": "Review ID already exists"}

        # Check unit_id validity
        if unit_id not in self.business_units:
            return {"success": False, "error": "Business unit does not exist"}

        # Check customer_id validity
        if customer_id not in self.customers:
            return {"success": False, "error": "Customer does not exist"}
    
        # Check for one-review-per-unit-per-customer
        for r in self.reviews.values():
            if r["unit_id"] == unit_id and r["customer_id"] == customer_id:
                return {"success": False, "error": "Customer has already reviewed this unit"}

        # (Optional: check customer verification status, if implemented)
        # For now, accept all customers as verified unless profile_info/status field is present.

        # Add the review
        self.reviews[review_id] = {
            "review_id": review_id,
            "unit_id": unit_id,
            "customer_id": customer_id,
            "rating": rating,
            "review_text": review_text,
            "timestamp": timestamp,
        }

        # Trigger reputation metric recompute for this unit if supported
        if hasattr(self, "recompute_reputation_metrics_for_unit"):
            self.recompute_reputation_metrics_for_unit(unit_id)

        return {"success": True, "message": "Review added"}

    def update_review(
        self,
        review_id: str,
        rating: Optional[float] = None,
        review_text: Optional[str] = None
    ) -> dict:
        """
        Update an existing review's rating and/or review text.

        Args:
            review_id (str): The unique identifier of the review to be updated.
            rating (Optional[float]): The new rating score (if updating).
            review_text (Optional[str]): The new review text (if updating).

        Returns:
            dict: 
                On success: { "success": True, "message": "Review updated successfully." }
                On error:   { "success": False, "error": "reason" }

        Constraints:
            - At least one of rating or review_text must be provided.
            - If rating is provided, it must be a float.
            - After update, must recompute reputation metrics for the associated business unit.
        """
        if review_id not in self.reviews:
            return { "success": False, "error": "Review ID does not exist." }

        if rating is None and review_text is None:
            return { "success": False, "error": "No fields to update (rating or review_text required)." }

        review = self.reviews[review_id]
    
        updated = False
        # Update fields if present
        if rating is not None:
            if not isinstance(rating, (float, int)):
                return { "success": False, "error": "Invalid rating type; must be a number." }
            review["rating"] = float(rating)
            updated = True

        if review_text is not None:
            if not isinstance(review_text, str):
                return { "success": False, "error": "review_text must be a string." }
            review["review_text"] = review_text
            updated = True

        if not updated:
            return { "success": False, "error": "No valid update provided." }
    
        # Store back updated review (not strictly needed since dict is by reference)
        self.reviews[review_id] = review

        # Recompute the reputation metrics for the unit (per constraints)
        unit_id = review["unit_id"]
        if hasattr(self, "recompute_reputation_metrics_for_unit"):
            self.recompute_reputation_metrics_for_unit(unit_id)
        # If method not present, just skip (graceful fallback)

        return { "success": True, "message": "Review updated successfully." }

    def remove_review(self, review_id: str) -> dict:
        """
        Delete a review by its review_id and trigger a reputation metric update for the unit.

        Args:
            review_id (str): The unique identifier for the review to delete.

        Returns:
            dict: {
                "success": True,
                "message": str  # Confirmation of deletion and metric update,
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Review must exist.
            - Reputation metrics for the associated business unit are recomputed after review removal.
        """
        review = self.reviews.get(review_id)
        if not review:
            return { "success": False, "error": "Review not found" }
    
        unit_id = review["unit_id"]
        # Remove review
        del self.reviews[review_id]
    
        # Recompute metrics for the unit
        ratings = [
            r["rating"] for r in self.reviews.values() if r["unit_id"] == unit_id
        ]
        if unit_id in self.business_units:
            unit = self.business_units[unit_id]
            if ratings:
                # Simple average for star rating; Trust score as average or can be same as star_rating if no details
                avg_rating = sum(ratings) / len(ratings)
                trust_score = avg_rating  # Here, trust_score and star_rating both use average rating as proxy
            else:
                avg_rating = 0.0
                trust_score = 0.0
            unit["star_rating"] = avg_rating
            unit["trust_score"] = trust_score
        
        return {
            "success": True,
            "message": f"Review {review_id} deleted and reputation metrics updated."
        }

    def add_business_unit(
        self,
        unit_id: str,
        business_id: str,
        name: str,
        address: str,
        web_link: str,
        trust_score: float = 0.0,
        star_rating: float = 0.0
    ) -> dict:
        """
        Register a new business unit under a parent business.

        Args:
            unit_id (str): Unique identifier for the new business unit.
            business_id (str): Parent business identifier (must exist).
            name (str): Name of the business unit.
            address (str): Address of the unit.
            web_link (str): Unique web link for the business unit.
            trust_score (float, optional): Initial trust score (default 0.0).
            star_rating (float, optional): Initial star rating (default 0.0).

        Returns:
            dict: 
                On success:
                    { "success": True, "message": "Business unit <unit_id> added under business <business_id>" }
                On failure:
                    { "success": False, "error": "<reason>" }

        Constraints:
            - Parent business must exist.
            - web_link must be globally unique among units and well-formed.
            - unit_id must not already exist.
        """
        # Check unique unit_id
        if unit_id in self.business_units:
            return {"success": False, "error": f"Business unit with id '{unit_id}' already exists"}

        # Check parent business exists
        if business_id not in self.businesses:
            return {"success": False, "error": f"Parent business '{business_id}' does not exist"}

        # Enforce web_link uniqueness
        if any(unit["web_link"] == web_link for unit in self.business_units.values()):
            return {"success": False, "error": "Web link already in use by another business unit"}

        # Optional: basic validation for web_link being a well-formed URL
        if not (web_link.startswith("http://") or web_link.startswith("https://")):
            return {"success": False, "error": "Web link must start with 'http://' or 'https://'"}     

        # Create and insert new business unit
        self.business_units[unit_id] = {
            "unit_id": unit_id,
            "business_id": business_id,
            "name": name,
            "address": address,
            "web_link": web_link,
            "trust_score": trust_score,
            "star_rating": star_rating,
        }
        return {"success": True, "message": f"Business unit {unit_id} added under business {business_id}"}

    def update_business_unit_web_link(self, unit_id: str, new_web_link: str) -> dict:
        """
        Change the web link of a business unit, ensuring the new link is unique and well-formed.

        Args:
            unit_id (str): Identifier of the business unit to update.
            new_web_link (str): The new web link (must be unique and valid URL).

        Returns:
            dict: {
                'success': True,
                'message': 'Web link updated for business unit <unit_id>'
            }
            or
            {
                'success': False,
                'error': <error message>
            }

        Constraints:
            - unit_id must exist in the system.
            - new_web_link must not be used by any other business unit.
            - new_web_link must be a well-formed URL (begins with 'http://' or 'https://', contains a '.').
        """
        # Check that the business unit exists
        if unit_id not in self.business_units:
            return { "success": False, "error": f"Business unit '{unit_id}' does not exist" }

        # Check URL validity (simple check)
        if not (isinstance(new_web_link, str) and
                (new_web_link.startswith("http://") or new_web_link.startswith("https://")) and
                "." in new_web_link.split("://", 1)[-1]):
            return { "success": False, "error": "Provided web link is not a valid URL" }

        # Check uniqueness (exclude the current unit)
        for uid, unit in self.business_units.items():
            if uid != unit_id and unit["web_link"] == new_web_link:
                return { "success": False, "error": "Web link is already in use by another business unit" }

        # Set/update the web link
        self.business_units[unit_id]["web_link"] = new_web_link

        return { "success": True, "message": f"Web link updated for business unit {unit_id}" }

    def add_business(self, business_id: str, name: str, industry: str, contact_info: str) -> dict:
        """
        Add/register a new business entity on the platform.

        Args:
            business_id (str): Unique identifier for the business.
            name (str): Business name.
            industry (str): Business industry.
            contact_info (str): Contact details (address, phone, email, etc.).

        Returns:
            dict: On success:
                      { "success": True, "message": "Business <name> added with id <business_id>." }
                  On failure (e.g., duplicate ID):
                      { "success": False, "error": "Business with this ID already exists." }
        Constraints:
            - The business_id must be unique (not already in self.businesses).
            - All arguments are required (no missing values).
        """
        # Check required fields
        if not (business_id and name and industry and contact_info):
            return { 
                "success": False, 
                "error": "All fields (business_id, name, industry, contact_info) are required." 
            }

        if business_id in self.businesses:
            return { "success": False, "error": "Business with this ID already exists." }

        business_info = {
            "business_id": business_id,
            "name": name,
            "industry": industry,
            "contact_info": contact_info
        }
        self.businesses[business_id] = business_info
        return {
            "success": True,
            "message": f"Business {name} added with id {business_id}."
        }

    def link_business_unit_to_business(self, unit_id: str, business_id: str) -> dict:
        """
        Set or update the parent business for a business unit.
        Enforces that only one parent is allowed per unit.

        Args:
            unit_id (str): ID of the business unit to update.
            business_id (str): ID of the business to link as parent.

        Returns:
            dict: {
                "success": True,
                "message": "Business unit <unit_id> is now linked to business <business_id>."
            }
            OR
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
        - business_id must reference an existing business in the platform.
        - unit_id must reference an existing business unit in the platform.
        - Each business unit can have only one parent business (this link will overwrite any previous association).
        """

        # Make sure the business unit exists
        if unit_id not in self.business_units:
            return {"success": False, "error": "Business unit does not exist"}

        # Make sure the business exists
        if business_id not in self.businesses:
            return {"success": False, "error": "Business does not exist"}

        # Update the parent business for the unit
        prev_business_id = self.business_units[unit_id]["business_id"]
        self.business_units[unit_id]["business_id"] = business_id

        if prev_business_id == business_id:
            return {
                "success": True,
                "message": f"Business unit {unit_id} was already linked to business {business_id}."
            }
        else:
            return {
                "success": True,
                "message": f"Business unit {unit_id} is now linked to business {business_id}."
            }

    def unlink_business_unit_from_business(self, unit_id: str) -> dict:
        """
        Remove the association between a business unit and its parent business.

        Args:
            unit_id (str): The unique identifier of the business unit to unlink.

        Returns:
            dict: 
                - On success: {"success": True, "message": "Business unit <unit_id> successfully unlinked from business <business_id>."}
                - On failure: {"success": False, "error": <reason>}

        Constraints:
            - The business unit must exist.
            - The business unit must currently be linked to a business.
            - This will clear the business_id from the business unit.
        """
        if unit_id not in self.business_units:
            return {"success": False, "error": "Business unit does not exist."}

        current_business_id = self.business_units[unit_id].get("business_id")

        if not current_business_id:
            return {"success": False, "error": "Business unit is already unlinked from any business."}

        self.business_units[unit_id]["business_id"] = ""
        return {
            "success": True,
            "message": f"Business unit {unit_id} successfully unlinked from business {current_business_id}."
        }

    def remove_business_unit(self, unit_id: str) -> dict:
        """
        Removes the specified business unit and all its associated reviews from the platform.

        Args:
            unit_id (str): The unique ID of the business unit to be removed.

        Returns:
            dict: {
                "success": True,
                "message": "Business unit <unit_id> and its reviews removed."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - All reviews associated with this unit must be deleted.
            - If the unit does not exist, operation fails.
        """
        # Check for existence
        if unit_id not in self.business_units:
            return { "success": False, "error": f"Business unit {unit_id} does not exist" }

        # Remove associated reviews
        review_ids_to_remove = [rid for rid, rinfo in self.reviews.items() if rinfo["unit_id"] == unit_id]
        for rid in review_ids_to_remove:
            del self.reviews[rid]

        # Remove the business unit itself
        del self.business_units[unit_id]

        return {
            "success": True,
            "message": f"Business unit {unit_id} and its reviews removed."
        }


class BusinessReputationReviewPlatform(BaseEnv):
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
            if key == "recompute_reputation_metrics_for_unit":
                setattr(env, "_recompute_reputation_metrics_for_unit_state", copy.deepcopy(value))
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

    def get_business_unit_by_id(self, **kwargs):
        return self._call_inner_tool('get_business_unit_by_id', kwargs)

    def get_business_unit_by_name(self, **kwargs):
        return self._call_inner_tool('get_business_unit_by_name', kwargs)

    def get_business_units_by_business(self, **kwargs):
        return self._call_inner_tool('get_business_units_by_business', kwargs)

    def get_trust_score_and_rating_for_unit(self, **kwargs):
        return self._call_inner_tool('get_trust_score_and_rating_for_unit', kwargs)

    def get_web_link_for_unit(self, **kwargs):
        return self._call_inner_tool('get_web_link_for_unit', kwargs)

    def get_reviews_for_unit(self, **kwargs):
        return self._call_inner_tool('get_reviews_for_unit', kwargs)

    def get_review_by_id(self, **kwargs):
        return self._call_inner_tool('get_review_by_id', kwargs)

    def get_business_by_id(self, **kwargs):
        return self._call_inner_tool('get_business_by_id', kwargs)

    def get_customer_by_id(self, **kwargs):
        return self._call_inner_tool('get_customer_by_id', kwargs)

    def list_all_businesses(self, **kwargs):
        return self._call_inner_tool('list_all_businesses', kwargs)

    def list_all_business_units(self, **kwargs):
        return self._call_inner_tool('list_all_business_units', kwargs)

    def recompute_reputation_metrics_for_unit(self, **kwargs):
        return self._call_inner_tool('recompute_reputation_metrics_for_unit', kwargs)

    def add_review(self, **kwargs):
        return self._call_inner_tool('add_review', kwargs)

    def update_review(self, **kwargs):
        return self._call_inner_tool('update_review', kwargs)

    def remove_review(self, **kwargs):
        return self._call_inner_tool('remove_review', kwargs)

    def add_business_unit(self, **kwargs):
        return self._call_inner_tool('add_business_unit', kwargs)

    def update_business_unit_web_link(self, **kwargs):
        return self._call_inner_tool('update_business_unit_web_link', kwargs)

    def add_business(self, **kwargs):
        return self._call_inner_tool('add_business', kwargs)

    def link_business_unit_to_business(self, **kwargs):
        return self._call_inner_tool('link_business_unit_to_business', kwargs)

    def unlink_business_unit_from_business(self, **kwargs):
        return self._call_inner_tool('unlink_business_unit_from_business', kwargs)

    def remove_business_unit(self, **kwargs):
        return self._call_inner_tool('remove_business_unit', kwargs)
