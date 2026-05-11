# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



class ProductInfo(TypedDict):
    product_id: str
    name: str
    category: str
    tags: List[str]
    description: str
    price: float
    stock_quantity: int
    image: List[str]  # supports multiple images

class ProductRatingInfo(TypedDict):
    product_id: str
    average_rating: float
    num_reviews: int

class ProductReviewInfo(TypedDict):
    product_id: str
    review_id: str
    customer_id: str
    rating: float
    review_text: str
    review_date: str  # Can also be datetime in further implementation

class _GeneratedEnvImpl:
    def __init__(self):
        """
        E-commerce Product Catalog & Inventory System

        Constraints/rules:
        - Only products with stock_quantity > 0 are considered “available”
        - Product search/query supports filters by keyword, category, tags, and price range
        - Sorting results by customer rating uses ProductRatingInfo.average_rating (descending)
        - Detailed product views must display name, description, price, stock status, and images
        """

        # Products: {product_id: ProductInfo}
        # From entity Product: product_id, name, category, tags, description, price, stock_quantity, image
        self.products: Dict[str, ProductInfo] = {}

        # Product Ratings: {product_id: ProductRatingInfo}
        # From entity ProductRating: product_id, average_rating, num_reviews
        self.product_ratings: Dict[str, ProductRatingInfo] = {}

        # Product Reviews: {review_id: ProductReviewInfo}
        # From entity ProductReview: product_id, review_id, customer_id, rating, review_text, review_date
        self.product_reviews: Dict[str, ProductReviewInfo] = {}

    def search_products_by_keyword(self, keyword: str) -> dict:
        """
        Search for available products whose name, description, category, or tags contain the given keyword (case-insensitive).

        Args:
            keyword (str): The keyword to search for (must not be empty or whitespace).

        Returns:
            dict:
                success (bool): True on success, False if invalid keyword.
                data (List[str]): List of matching product_ids (may be empty if no matches).
                error (str, optional): If failed, the error reason.

        Constraints:
            - Only available products (stock_quantity > 0) are considered.
            - Keyword is matched case-insensitively in name, description, category, or tags.
            - If keyword is empty or only whitespace, returns error.
        """
        if not isinstance(keyword, str) or not keyword.strip():
            return {"success": False, "error": "Keyword must be a non-empty string."}

        norm_keyword = keyword.strip().lower()
        matched_products = []

        for product in self.products.values():
            if product["stock_quantity"] <= 0:
                continue  # Ignore unavailable products

            # Prepare lower-cased fields for matching
            name = product["name"].lower()
            description = product["description"].lower()
            category = product["category"].lower()
            tags = [tag.lower() for tag in product["tags"]]

            # Match keyword in name, description, category, or tags
            if (norm_keyword in name or
                norm_keyword in description or
                norm_keyword in category or
                any(norm_keyword in tag for tag in tags)):
                matched_products.append(product["product_id"])

        return {"success": True, "data": matched_products}

    def filter_products_by_category(self, category: str) -> dict:
        """
        Filter and return all available (stock_quantity > 0) products belonging to the specified category.

        Args:
            category (str): The category to filter products by.

        Returns:
            dict: {
                "success": True,
                "data": List[ProductInfo]  # May be empty if no products match
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., missing or invalid category
            }

        Constraints:
            - Only available products (stock_quantity > 0) are included in the result.
        """
        if not isinstance(category, str) or not category.strip():
            return { "success": False, "error": "Invalid or missing category." }

        filtered = [
            product
            for product in self.products.values()
            if product["category"] == category and product["stock_quantity"] > 0
        ]
        return { "success": True, "data": filtered }

    def filter_products_by_tags(self, tags: list) -> dict:
        """
        Filter products by one or more tags.

        Args:
            tags (list of str): The list of tags to filter products by.
                If empty, all products are returned.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[ProductInfo]  # possibly empty if no matches
                }
                or
                {
                    "success": False,
                    "error": str  # If tags input is not a list
                }

        Constraints:
            - Products included if they have at least one tag in common with the input tags.
            - If tags is empty, all products are returned.
        """
        if not isinstance(tags, list):
            return {"success": False, "error": "Input 'tags' must be a list of strings."}

        # If tags is empty, return all products
        if not tags:
            result = list(self.products.values())
            return {"success": True, "data": result}

        # Otherwise, filter for products with any of the tags
        tag_set = set(tags)
        result = [
            product for product in self.products.values()
            if tag_set.intersection(set(product.get("tags", [])))
        ]
        return {"success": True, "data": result}

    def filter_products_by_price_range(self, min_price: float, max_price: float) -> dict:
        """
        Filter and retrieve all products whose price falls within a given inclusive range.

        Args:
            min_price (float): Minimum price (inclusive).
            max_price (float): Maximum price (inclusive).

        Returns:
            dict: {
                "success": True,
                "data": List[ProductInfo]  # List of ProductInfo for products in price range
            }
            or
            {
                "success": False,
                "error": str  # Error message if invalid input
            }

        Constraints:
            - min_price and max_price must be non-negative.
            - min_price must be less than or equal to max_price.
        """
        if not isinstance(min_price, (int, float)) or not isinstance(max_price, (int, float)):
            return {"success": False, "error": "Price bounds must be numeric values"}

        if min_price < 0 or max_price < 0:
            return {"success": False, "error": "Price bounds must be non-negative"}
        if min_price > max_price:
            return {"success": False, "error": "min_price cannot be greater than max_price"}

        filtered = [
            product for product in self.products.values()
            if min_price <= product["price"] <= max_price
        ]

        return {"success": True, "data": filtered}

    def filter_products_by_availability(self) -> dict:
        """
        Retrieve all products that are currently available (stock_quantity > 0).

        Returns:
            dict: {
                "success": True,
                "data": List[ProductInfo]  # List of available products
            }

        Constraints:
            - Only products with stock_quantity > 0 are listed as available.
            - Returns empty list if no products available or catalog is empty.
        """
        available_products = [
            product for product in self.products.values()
            if product["stock_quantity"] > 0
        ]
        return { "success": True, "data": available_products }

    def get_product_rating(self, product_id: str) -> dict:
        """
        Retrieve the aggregate customer rating (average_rating, num_reviews) for a given product.

        Args:
            product_id (str): The product's unique identifier.

        Returns:
            dict: 
                {"success": True, "data": ProductRatingInfo} if found,
                {"success": False, "error": "Product rating not found"} if not found.

        Constraints:
            - product_id must refer to a product that has rating information.
        """
        rating_info = self.product_ratings.get(product_id)
        if rating_info is None:
            return {"success": False, "error": "Product rating not found"}

        return {"success": True, "data": rating_info}

    def sort_products_by_rating(self, product_ids: list[str]) -> dict:
        """
        Sort a list of product_ids by their average customer rating in descending order.

        Args:
            product_ids (list[str]): List of product IDs to sort.
                - Invalid product IDs (not in self.products) are ignored.
                - Products without a rating are treated as rating=0.

        Returns:
            dict:
                - "success": True
                - "data": List[str] -- Sorted (desc) product_ids by rating, only those found in self.products.
            or
                - "success": False
                - "error": str (for unexpected input)

        Constraints:
            - Only existing products are included.
            - Empty input list returns success with empty result.
        """
        if not isinstance(product_ids, list):
            return { "success": False, "error": "Input product_ids must be a list of strings" }

        # Filter only product_ids that exist in the catalog
        valid_ids = [pid for pid in product_ids if pid in self.products]
        ratings = []
        for pid in valid_ids:
            rating_info = self.product_ratings.get(pid)
            avg_rating = rating_info["average_rating"] if rating_info else 0.0
            ratings.append((pid, avg_rating))

        # Sort by rating descending; preserve input order for ties
        sorted_ratings = sorted(ratings, key=lambda x: x[1], reverse=True)
        sorted_product_ids = [pid for pid, _ in sorted_ratings]

        return { "success": True, "data": sorted_product_ids }

    def get_product_details(self, product_id: str) -> dict:
        """
        Retrieve detailed product information for a given product_id.
    
        Args:
            product_id (str): The ID of the product to query.
    
        Returns:
            dict: {
                "success": True,
                "data": {
                    "product_id": str,
                    "name": str,
                    "description": str,
                    "tags": List[str],
                    "price": float,
                    "stock_status": str,   # "available" or "unavailable"
                    "stock_quantity": int, # remaining number
                    "images": List[str]
                }
            }
            or
            {
                "success": False,
                "error": "Product not found"
            }
    
        Constraints:
            - Product must exist in the catalog.
            - Stock status: "available" if stock_quantity > 0, else "unavailable".
        """
        product = self.products.get(product_id)
        if not product:
            return {"success": False, "error": "Product not found"}
    
        stock_status = "available" if product["stock_quantity"] > 0 else "unavailable"
    
        data = {
            "product_id": product["product_id"],
            "name": product["name"],
            "description": product["description"],
            "tags": copy.deepcopy(product["tags"]),
            "price": product["price"],
            "stock_status": stock_status,
            "stock_quantity": product["stock_quantity"],
            "images": product["image"]
        }
        return {"success": True, "data": data}

    def get_multiple_products_details(self, product_ids: list[str]) -> dict:
        """
        Retrieve detailed information for multiple products (batch variant).
        For each specified product_id, returns:
            - name
            - description
            - price
            - availability ("available" if stock_quantity > 0 else "not available")
            - image (list of image urls/paths)

        Args:
            product_ids (List[str]): List of product IDs to retrieve details for.

        Returns:
            dict: {
                "success": True,
                "data": List[Dict]  # Each dict: {"product_id", "name", "description", "price", "availability", "images"}
            }

        Constraints:
            - If a product_id does not exist, it is skipped (not included in results).
            - If no valid products are found, returns empty list with success=True.
        """
        details_list = []
        for pid in product_ids:
            product = self.products.get(pid)
            if not product:
                continue  # skip non-existing product_ids
            details = {
                "product_id": product["product_id"],
                "name": product["name"],
                "description": product["description"],
                "price": product["price"],
                "availability": "available" if product["stock_quantity"] > 0 else "not available",
                "images": product["image"]
            }
            details_list.append(details)
        return {"success": True, "data": details_list}

    def get_product_reviews(self, product_id: str) -> dict:
        """
        Retrieve all customer reviews for the specified product.

        Args:
            product_id (str): The unique identifier of the product.

        Returns:
            dict:
                - On success: {
                    "success": True,
                    "data": List[ProductReviewInfo]  # List of review dicts (empty if no reviews)
                  }
                - On failure: {
                    "success": False,
                    "error": str   # e.g., "Product does not exist."
                  }

        Constraints:
            - The given product_id must exist in the product catalog.
        """
        if product_id not in self.products:
            return { "success": False, "error": "Product does not exist." }
    
        reviews = [
            review for review in self.product_reviews.values()
            if review["product_id"] == product_id
        ]
        return { "success": True, "data": reviews }

    def get_top_n_products(self, n: int) -> dict:
        """
        Retrieve the top N available products, sorted by average customer rating (descending).
        Only products with stock_quantity > 0 are considered "available".
        Products without ratings are included but sorted lower (average_rating=0).

        Args:
            n (int): Number of top products to return (must be positive integer).

        Returns:
            dict: {
                "success": True,
                "data": List[ProductInfo], # Up to n entries (may be fewer)
            }
            or
            {
                "success": False,
                "error": str # Description of the error (e.g. invalid n)
            }
        """
        # Validate input
        if not isinstance(n, int) or n <= 0:
            return { "success": False, "error": "Parameter n must be a positive integer." }

        # Build list of available products with rating info
        available_products = []
        for product in self.products.values():
            if product.get("stock_quantity", 0) > 0:
                rating_info = self.product_ratings.get(product["product_id"])
                avg_rating = rating_info["average_rating"] if rating_info else 0.0
                num_reviews = rating_info["num_reviews"] if rating_info else 0
                available_products.append((
                    avg_rating,
                    num_reviews,
                    product["name"],  # For stable sort
                    product         # The actual product info
                ))

        # Sort: by avg_rating descending, then num_reviews descending, then name ascending
        available_products.sort(reverse=True, key=lambda x: (x[0], x[1], x[2]))

        # Get up to n products
        top_n_products = [prod[3] for prod in available_products[:n]]

        return {
            "success": True,
            "data": top_n_products
        }

    def update_product_stock(self, product_id: str, new_stock_quantity: int) -> dict:
        """
        Modify the stock_quantity of a specified product.

        Args:
            product_id (str): The identifier of the product to update.
            new_stock_quantity (int): The new stock level to be set (must be >= 0).

        Returns:
            dict: {
                "success": True,
                "message": "Stock for product <product_id> updated to <new_stock_quantity>."
            }
            or
            {
                "success": False,
                "error": "<reason for failure>"
            }

        Constraints:
            - product_id must exist in the system.
            - new_stock_quantity must be non-negative (>= 0).
        """
        # Check for product existence
        if product_id not in self.products:
            return { "success": False, "error": f"Product {product_id} does not exist." }

        # Check for non-negative stock
        if not isinstance(new_stock_quantity, int) or new_stock_quantity < 0:
            return { "success": False, "error": "Stock quantity must be a non-negative integer." }

        # Update stock
        self.products[product_id]["stock_quantity"] = new_stock_quantity

        return {
            "success": True,
            "message": f"Stock for product {product_id} updated to {new_stock_quantity}."
        }

    def add_new_product(
        self,
        product_id: str,
        name: str,
        category: str,
        tags: list,
        description: str,
        price: float,
        stock_quantity: int,
        image: list
    ) -> dict:
        """
        Add a new product to the catalog.

        Args:
            product_id (str): Unique identifier for the product
            name (str): Name of the product
            category (str): Product category
            tags (List[str]): List of product tags
            description (str): Product description
            price (float): Product price (must be >= 0)
            stock_quantity (int): Product stock quantity (must be >= 0)
            image (List[str]): List of image URLs or paths

        Returns:
            dict:
                - success (bool): True if added, False if not
                - message (str): Success message (if success)
                - error (str): Error message (if failure)

        Constraints:
            - product_id must be unique
            - price and stock_quantity cannot be negative
        """
        # Check for existing product_id
        if product_id in self.products:
            return { "success": False, "error": "Product ID already exists." }
    
        # Type and value checks
        if not isinstance(product_id, str) or not product_id.strip():
            return { "success": False, "error": "Invalid or missing product_id." }
        if not isinstance(name, str) or not name.strip():
            return { "success": False, "error": "Invalid or missing name." }
        if not isinstance(category, str) or not category.strip():
            return { "success": False, "error": "Invalid or missing category." }
        if not isinstance(tags, list):
            return { "success": False, "error": "Tags must be a list." }
        if not isinstance(description, str):
            return { "success": False, "error": "Invalid or missing description." }
        if not isinstance(price, (float, int)) or price < 0:
            return { "success": False, "error": "Price must be a non-negative number." }
        if not isinstance(stock_quantity, int) or stock_quantity < 0:
            return { "success": False, "error": "Stock quantity must be a non-negative integer." }
        if not isinstance(image, list):
            return { "success": False, "error": "Image must be a list of image URLs or file paths." }

        # Build ProductInfo
        product_info: ProductInfo = {
            "product_id": product_id,
            "name": name,
            "category": category,
            "tags": tags,
            "description": description,
            "price": float(price),
            "stock_quantity": stock_quantity,
            "image": image
        }
        self.products[product_id] = product_info

        return { "success": True, "message": f"Product {product_id} added successfully." }

    def update_product_info(self, product_id: str, updates: dict) -> dict:
        """
        Update one or more mutable attributes of an existing product.

        Args:
            product_id (str): The unique product identifier.
            updates (dict): Keys/values for fields to update. Allowed fields:
                name (str), category (str), tags (List[str]), description (str),
                price (float, >=0), stock_quantity (int, >=0), image (List[str])

        Returns:
            dict: {
                "success": True,
                "message": "Product info updated for <product_id>"
            }
            OR
            {
                "success": False,
                "error": str
            }

        Constraints:
            - product_id must exist.
            - Only valid fields allowed; product_id cannot be updated.
            - price and stock_quantity must be non-negative.
            - Data types of fields must match schema.
        """
        # Check product existence
        if product_id not in self.products:
            return { "success": False, "error": "Product not found." }

        allowed_fields = {
            "name": str,
            "category": str,
            "tags": list,
            "description": str,
            "price": float,
            "stock_quantity": int,
            "image": list
        }
        if not updates:
            return {"success": False, "error": "No update fields provided."}

        invalid_fields = [k for k in updates.keys() if k not in allowed_fields]
        if invalid_fields:
            return {"success": False, "error": f"Invalid field(s): {', '.join(invalid_fields)}"}

        # Validate and set
        product = self.products[product_id]
        for key, value in updates.items():
            expected_type = allowed_fields[key]
            # Special type handling for price/int
            if key == "price":
                if not (isinstance(value, (int, float)) and value >= 0):
                    return {"success": False, "error": "Price must be a non-negative number."}
            elif key == "stock_quantity":
                if not (isinstance(value, int) and value >= 0):
                    return {"success": False, "error": "Stock quantity must be a non-negative integer."}
            elif key in ("tags", "image"):
                if not (isinstance(value, list) and all(isinstance(i, str) for i in value)):
                    return {"success": False, "error": f"{key} must be a list of strings."}
            else:
                if not isinstance(value, expected_type):
                    return {"success": False, "error": f"Field '{key}' should be of type {expected_type.__name__}."}
            # Passed validation, update
            product[key] = value

        self.products[product_id] = product
        return { "success": True, "message": f"Product info updated for {product_id}" }

    def add_product_review(
        self,
        product_id: str,
        review_id: str,
        customer_id: str,
        rating: float,
        review_text: str,
        review_date: str
    ) -> dict:
        """
        Add a new review for a product.

        Args:
            product_id (str): Product being reviewed (must exist).
            review_id (str): Unique review identifier (must not exist).
            customer_id (str): Customer writing the review.
            rating (float): The rating score (expected: 0 <= rating <= 5).
            review_text (str): The content of the review.
            review_date (str): Date of the review (format not strictly checked).

        Returns:
            dict: {
                "success": True,
                "message": "Review added to product <product_id>."
            }
            OR
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - product_id must exist.
            - review_id must be unique.
            - 0 <= rating <= 5.
            - Updates ProductRatingInfo for the product accordingly.
        """

        # Check if product exists
        if product_id not in self.products:
            return {"success": False, "error": "Product does not exist."}

        # Check uniqueness of review_id
        if review_id in self.product_reviews:
            return {"success": False, "error": "Review ID already exists."}

        # Validate rating (assuming 0–5 stars system)
        if not (0.0 <= rating <= 5.0):
            return {"success": False, "error": "Rating must be between 0 and 5."}

        # Add the new review
        new_review = {
            "product_id": product_id,
            "review_id": review_id,
            "customer_id": customer_id,
            "rating": rating,
            "review_text": review_text,
            "review_date": review_date,
        }
        self.product_reviews[review_id] = new_review

        # Update product_ratings for the product
        # If no rating exists, initialize
        if product_id not in self.product_ratings:
            self.product_ratings[product_id] = {
                "product_id": product_id,
                "average_rating": rating,
                "num_reviews": 1
            }
        else:
            rating_info = self.product_ratings[product_id]
            n = rating_info["num_reviews"]
            avg = rating_info["average_rating"]
            new_avg = (avg * n + rating) / (n + 1)
            self.product_ratings[product_id]["average_rating"] = new_avg
            self.product_ratings[product_id]["num_reviews"] = n + 1

        return {"success": True, "message": f"Review added to product {product_id}."}

    def recalculate_product_rating(self, product_id: str) -> dict:
        """
        Recompute a product's aggregate (average) rating and number of reviews
        based on all its customer reviews. Updates the product_ratings entry.

        Args:
            product_id (str): The product whose rating should be recalculated.

        Returns:
            dict: {
                "success": True,
                "message": f"Aggregate rating updated to {average_rating} with {num_reviews} reviews."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Product must exist in the catalog.
            - If no reviews are present, average_rating is set to 0.0 and num_reviews to 0.
        """
        if product_id not in self.products:
            return {"success": False, "error": "Product does not exist."}

        # Get all reviews for the product
        reviews = [
            review for review in self.product_reviews.values()
            if review["product_id"] == product_id
        ]

        num_reviews = len(reviews)
        if num_reviews == 0:
            average_rating = 0.0
        else:
            total_rating = sum(review["rating"] for review in reviews)
            average_rating = total_rating / num_reviews

        # Update or create the ProductRatingInfo entry
        self.product_ratings[product_id] = {
            "product_id": product_id,
            "average_rating": average_rating,
            "num_reviews": num_reviews
        }

        return {
            "success": True,
            "message": (
                f"Aggregate rating updated to {average_rating:.2f} "
                f"with {num_reviews} review{'s' if num_reviews != 1 else ''}."
            )
        }

    def remove_product(self, product_id: str) -> dict:
        """
        Remove a product and associated information from the catalog.

        Args:
            product_id (str): The ID of the product to remove.

        Returns:
            dict:
              - success: True and message describing operation when product is removed,
              - or, success: False and error describing why failed.

        Constraints:
            - If the product does not exist, operation fails.
            - Removes product, its rating info, and all its reviews.
        """
        # Check that product exists
        if product_id not in self.products:
            return {"success": False, "error": "Product does not exist"}

        # Remove product entry
        del self.products[product_id]

        # Remove product rating info, if present
        if product_id in self.product_ratings:
            del self.product_ratings[product_id]

        # Remove all reviews for the product
        review_ids_to_remove = [review_id for review_id, review in self.product_reviews.items() if review["product_id"] == product_id]
        for review_id in review_ids_to_remove:
            del self.product_reviews[review_id]

        return {"success": True, "message": f"Product '{product_id}' and associated data removed from catalog"}


class EcommerceProductCatalogInventory(BaseEnv):
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

    def search_products_by_keyword(self, **kwargs):
        return self._call_inner_tool('search_products_by_keyword', kwargs)

    def filter_products_by_category(self, **kwargs):
        return self._call_inner_tool('filter_products_by_category', kwargs)

    def filter_products_by_tags(self, **kwargs):
        return self._call_inner_tool('filter_products_by_tags', kwargs)

    def filter_products_by_price_range(self, **kwargs):
        return self._call_inner_tool('filter_products_by_price_range', kwargs)

    def filter_products_by_availability(self, **kwargs):
        return self._call_inner_tool('filter_products_by_availability', kwargs)

    def get_product_rating(self, **kwargs):
        return self._call_inner_tool('get_product_rating', kwargs)

    def sort_products_by_rating(self, **kwargs):
        return self._call_inner_tool('sort_products_by_rating', kwargs)

    def get_product_details(self, **kwargs):
        return self._call_inner_tool('get_product_details', kwargs)

    def get_multiple_products_details(self, **kwargs):
        return self._call_inner_tool('get_multiple_products_details', kwargs)

    def get_product_reviews(self, **kwargs):
        return self._call_inner_tool('get_product_reviews', kwargs)

    def get_top_n_products(self, **kwargs):
        return self._call_inner_tool('get_top_n_products', kwargs)

    def update_product_stock(self, **kwargs):
        return self._call_inner_tool('update_product_stock', kwargs)

    def add_new_product(self, **kwargs):
        return self._call_inner_tool('add_new_product', kwargs)

    def update_product_info(self, **kwargs):
        return self._call_inner_tool('update_product_info', kwargs)

    def add_product_review(self, **kwargs):
        return self._call_inner_tool('add_product_review', kwargs)

    def recalculate_product_rating(self, **kwargs):
        return self._call_inner_tool('recalculate_product_rating', kwargs)

    def remove_product(self, **kwargs):
        return self._call_inner_tool('remove_product', kwargs)
