# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict, Optional



class ProductInfo(TypedDict):
    # product_id: str, name: str, description: str, category: str
    product_id: str
    name: str
    description: str
    category: str

class OfferInfo(TypedDict):
    # offer_id: str, product_id: str (FK), seller_id: str (FK), price: float, availability: bool, discount: Optional[float]
    offer_id: str
    product_id: str
    seller_id: str
    price: float
    availability: bool  # True if active/available
    discount: Optional[float]  # Percentage discount, 0-100. None if not present

class SellerInfo(TypedDict):
    # seller_id: str, name: str, rating: float
    seller_id: str
    name: str
    rating: float

class _GeneratedEnvImpl:
    def __init__(self):
        # Products: {product_id: ProductInfo}, represents all products in the catalog
        self.products: Dict[str, ProductInfo] = {}

        # Offers: {offer_id: OfferInfo}, represents all offers associated with products and sellers
        self.offers: Dict[str, OfferInfo] = {}

        # Sellers: {seller_id: SellerInfo}, represents all sellers in the system
        self.sellers: Dict[str, SellerInfo] = {}

        # Constraints (to be enforced in business logic):
        # - Every offer must be associated with an existing product.
        # - Product IDs and seller IDs must be unique system-wide.
        # - Availability controls whether an offer is currently active and can be shown to users.
        # - Discount (if present) must be within reasonable bounds (such as 0–100%).

    def get_product_by_id(self, product_id: str) -> dict:
        """
        Retrieve product details by product_id.

        Args:
            product_id (str): The unique identifier for the product.

        Returns:
            dict: {
                "success": True,
                "data": ProductInfo
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - product_id must exist in the catalog.
        """
        product = self.products.get(product_id)
        if not product:
            return { "success": False, "error": "Product not found" }
        return { "success": True, "data": product }

    def search_products_by_name(self, query: str) -> dict:
        """
        Search for products using their name (supports partial, case-insensitive matches).

        Args:
            query (str): Substring to search for in product names. If empty, returns all products.

        Returns:
            dict: {
                "success": True,
                "data": List[ProductInfo],  # List of products with names matching the query (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Explanation of the error
            }

        Constraints:
            - The query must be a string (may be empty).
        """
        if not isinstance(query, str):
            return { "success": False, "error": "Invalid query: must be a string." }

        query_lower = query.lower()
        result = [
            prod for prod in self.products.values()
            if query_lower in prod["name"].lower()
        ] if query else list(self.products.values())

        return { "success": True, "data": result }

    def list_offers_for_product(self, product_id: str) -> dict:
        """
        Retrieve all offers associated with the given product ID.

        Args:
            product_id (str): The unique identifier for the product.

        Returns:
            dict
                - If product exists, returns:
                    {
                        "success": True,
                        "data": [OfferInfo, ...]  # List of all associated offers (may be empty)
                    }
                - If product does not exist:
                    {
                        "success": False,
                        "error": "Product not found"
                    }
        Constraints:
            - The product_id must exist in the system.
            - Returned offers are only those whose product_id matches the query argument.
        """
        if product_id not in self.products:
            return {"success": False, "error": "Product not found"}

        offers = [
            offer for offer in self.offers.values()
            if offer["product_id"] == product_id
        ]
        return {"success": True, "data": offers}

    def list_available_offers_for_product(self, product_id: str) -> dict:
        """
        Retrieve all currently available (active) offers for a given product ID.

        Args:
            product_id (str): The unique identifier for the product.

        Returns:
            dict: {
                "success": True,
                "data": List[OfferInfo],  # List of available (active) OfferInfo for the product (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g., 'Product does not exist'
            }

        Constraints:
            - The product_id must correspond to an existing product in the catalog.
            - Only offers with availability == True are returned.
        """
        if product_id not in self.products:
            return { "success": False, "error": "Product does not exist" }

        available_offers = [
            offer for offer in self.offers.values()
            if offer["product_id"] == product_id and offer["availability"] is True
        ]

        return { "success": True, "data": available_offers }

    def get_offer_by_id(self, offer_id: str) -> dict:
        """
        Retrieve the full details for a specific offer by its unique offer_id.

        Args:
            offer_id (str): Unique identifier of the offer.

        Returns:
            dict: {
                "success": True,
                "data": OfferInfo  # Offer details
            }
            or
            {
                "success": False,
                "error": str  # "Offer not found"
            }

        Constraints:
            - The offer must exist (offer_id must be in self.offers).
        """
        offer = self.offers.get(offer_id)
        if not offer:
            return { "success": False, "error": "Offer not found" }
        return { "success": True, "data": offer }

    def get_seller_by_id(self, seller_id: str) -> dict:
        """
        Retrieve details for a seller, including seller_id, name, and rating, using the seller_id.

        Args:
            seller_id (str): The unique identifier of the seller.

        Returns:
            dict: {
                "success": True,
                "data": SellerInfo  # The seller info if found
            }
            or
            {
                "success": False,
                "error": str  # Error description if the seller is not found
            }

        Constraints:
            - The seller_id must exist in the system.
        """
        seller = self.sellers.get(seller_id)
        if seller is not None:
            return {"success": True, "data": seller}
        else:
            return {"success": False, "error": "Seller does not exist"}

    def list_sellers(self) -> dict:
        """
        List all sellers in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[SellerInfo],  # List of all seller infos (possibly empty list)
            }
        No input parameters.
        There are no constraints for this read operation.
        """
        seller_list = list(self.sellers.values())
        return {"success": True, "data": seller_list}

    def list_products_by_category(self, category: str) -> dict:
        """
        List all products under a given category.

        Args:
            category (str): The category name to filter products by. Case-sensitive.
    
        Returns:
            dict: {
                "success": True,
                "data": List[ProductInfo]  # Empty list if no products found
            }
            or
            {
                "success": False,
                "error": str  # Only if input is missing
            }
        Constraints:
            - Category match is exact and case-sensitive.
            - If category is empty or None, returns products with empty category field.
        """
        if category is None:
            return { "success": False, "error": "Category must be provided" }

        result = [
            prod for prod in self.products.values()
            if prod["category"] == category
        ]
        return { "success": True, "data": result }

    def get_discount_for_offer(self, offer_id: str) -> dict:
        """
        Retrieve the discount percentage for a given offer by offer_id, if available.

        Args:
            offer_id (str): The unique identifier of the offer.

        Returns:
            dict: {
                "success": True,
                "data": discount (float|None)  # Discount percentage 0–100, or None if not set
            }
            or
            {
                "success": False,
                "error": str  # Error message if offer_id is invalid/not found
            }

        Constraints:
            - Offer with the given offer_id must exist in the system.
        """
        offer = self.offers.get(offer_id)
        if offer is None:
            return { "success": False, "error": "Offer not found" }
        return { "success": True, "data": offer.get("discount") }

    def add_product(
        self,
        product_id: str,
        name: str,
        description: str,
        category: str
    ) -> dict:
        """
        Adds a new product to the product catalog.

        Args:
            product_id (str): Unique identifier for the product.
            name (str): The name of the product.
            description (str): Description of the product.
            category (str): Product category.

        Returns:
            dict:
                On success: { "success": True, "message": "Product added successfully" }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - Product IDs must be unique system-wide.
            - All fields are required and must be non-empty.
        """
        # Validate inputs
        if not all([product_id, name, description, category]):
            return { "success": False, "error": "All fields (product_id, name, description, category) are required and must be non-empty" }

        if product_id in self.products:
            return { "success": False, "error": "Product ID already exists" }

        new_product: ProductInfo = {
            "product_id": product_id,
            "name": name,
            "description": description,
            "category": category
        }
        self.products[product_id] = new_product

        return { "success": True, "message": "Product added successfully" }

    def remove_product(self, product_id: str) -> dict:
        """
        Remove a product from the catalog.
        Cannot remove if any offers are associated with the product.

        Args:
            product_id (str): The ID of the product to remove.

        Returns:
            dict: {
                "success": True,
                "message": str, # success message on successful removal
            }
            or
            {
                "success": False,
                "error": str # reason for failure
            }

        Constraints:
            - Product must exist in catalog.
            - Cannot remove if any offer points to the product.
        """
        # Check if product exists
        if product_id not in self.products:
            return {"success": False, "error": "Product does not exist."}

        # Check if any offers depend on this product
        for offer in self.offers.values():
            if offer["product_id"] == product_id:
                return {
                    "success": False,
                    "error": "Cannot remove product: offers associated with this product exist."
                }

        # Remove product
        del self.products[product_id]
        return {
            "success": True,
            "message": f"Product {product_id} removed successfully."
        }

    def add_offer(
        self,
        offer_id: str,
        product_id: str,
        seller_id: str,
        price: float,
        availability: bool,
        discount: Optional[float] = None
    ) -> dict:
        """
        Create a new offer for a product and seller.
    
        Args:
            offer_id (str): Unique ID for the offer (must not already exist).
            product_id (str): Must refer to an existing product.
            seller_id (str): Must refer to an existing seller.
            price (float): Offer price.
            availability (bool): Whether the offer is currently active.
            discount (Optional[float]): Optional discount percentage (0-100).

        Returns:
            dict: {
                "success": True,
                "message": "Offer added successfully"
            }
            or
            {
                "success": False,
                "error": <reason>
            }
    
        Constraints:
            - offer_id must be unique among offers.
            - product_id must exist in products.
            - seller_id must exist in sellers.
            - If discount is not None, must be between 0 and 100 (inclusive).
        """
        # Uniqueness check for offer_id
        if offer_id in self.offers:
            return { "success": False, "error": "Offer ID already exists" }
        # Check product_id existence
        if product_id not in self.products:
            return { "success": False, "error": "Product does not exist" }
        # Check seller_id existence
        if seller_id not in self.sellers:
            return { "success": False, "error": "Seller does not exist" }
        # Discount validity
        if discount is not None:
            if not (0 <= discount <= 100):
                return { "success": False, "error": "Discount must be between 0 and 100" }
    
        self.offers[offer_id] = {
            "offer_id": offer_id,
            "product_id": product_id,
            "seller_id": seller_id,
            "price": price,
            "availability": availability,
            "discount": discount
        }

        return { "success": True, "message": "Offer added successfully" }

    def update_offer_availability(self, offer_id: str, availability: bool) -> dict:
        """
        Change the 'availability' status of an offer by its offer_id.

        Args:
            offer_id (str): Unique identifier of the offer to update.
            availability (bool): New availability status (True = active, False = inactive).

        Returns:
            dict: {
                "success": True,
                "message": "Offer availability updated successfully"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The offer_id must exist in the system.
        """
        if offer_id not in self.offers:
            return { "success": False, "error": "Offer does not exist" }

        self.offers[offer_id]['availability'] = availability
        return { "success": True, "message": "Offer availability updated successfully" }

    def update_offer_price(self, offer_id: str, new_price: float) -> dict:
        """
        Update the price for a specific offer.

        Args:
            offer_id (str): The unique ID of the offer to update.
            new_price (float): The new price to set for this offer.

        Returns:
            dict: {
                "success": True,
                "message": "Offer price updated successfully."
            }
            or
            {
                "success": False,
                "error": <reason>,
            }

        Constraints:
            - Offer must exist.
            - New price must be non-negative.
        """
        if offer_id not in self.offers:
            return {"success": False, "error": "Offer does not exist."}

        if not isinstance(new_price, (float, int)) or new_price < 0:
            return {"success": False, "error": "Invalid new price. Must be a non-negative number."}

        self.offers[offer_id]["price"] = float(new_price)
        return {"success": True, "message": "Offer price updated successfully."}

    def update_offer_discount(self, offer_id: str, discount: float) -> dict:
        """
        Change the discount of an offer, enforcing it remains between 0 and 100 (inclusive).

        Args:
            offer_id (str): The unique identifier of the offer to update.
            discount (float or None): The new discount percentage (0–100), or None to clear discount.

        Returns:
            dict: {
                "success": True,
                "message": "Discount updated for offer <offer_id>"
            }
            OR
            {
                "success": False,
                "error": "<error reason>"
            }

        Constraints:
            - offer_id must exist in offers.
            - discount must be None or a float between 0 and 100 (inclusive).
        """
        if offer_id not in self.offers:
            return { "success": False, "error": "Offer does not exist" }

        # Accept None to clear discount
        if discount is None:
            self.offers[offer_id]["discount"] = None
            return { "success": True, "message": f"Discount cleared for offer {offer_id}" }

        # Validate type and range
        try:
            discount_val = float(discount)
        except (TypeError, ValueError):
            return { "success": False, "error": "Discount must be a number between 0 and 100 or None" }

        if not (0.0 <= discount_val <= 100.0):
            return { "success": False, "error": "Discount must be between 0 and 100" }

        self.offers[offer_id]["discount"] = discount_val
        return { "success": True, "message": f"Discount updated for offer {offer_id}" }

    def remove_offer(self, offer_id: str) -> dict:
        """
        Remove an offer from the system.

        Args:
            offer_id (str): The unique identifier of the offer to remove.

        Returns:
            dict:
                - On success: { "success": True, "message": "Offer <offer_id> removed." }
                - On failure: { "success": False, "error": "Offer does not exist." }

        Constraints:
            - The offer_id must exist in the system.
            - This does not affect associated products or sellers.
        """
        if offer_id not in self.offers:
            return { "success": False, "error": "Offer does not exist." }

        del self.offers[offer_id]
        return { "success": True, "message": f"Offer {offer_id} removed." }

    def add_seller(self, seller_id: str, name: str, rating: float) -> dict:
        """
        Register a new seller with a unique seller_id.

        Args:
            seller_id (str): Unique identifier for the seller. Must not already exist.
            name (str): Seller display name. Must not be empty.
            rating (float): Seller's rating (typically 0–5). Must be in this range.

        Returns:
            dict: {
                "success": True,
                "message": "Seller added successfully."
            }
            or
            {
                "success": False,
                "error": "Reason for failure."
            }

        Constraints:
            - seller_id must be unique system-wide.
            - name must not be empty.
            - rating must be between 0 and 5, inclusive.
        """
        if not seller_id or seller_id.strip() == "":
            return {"success": False, "error": "Seller ID cannot be empty."}

        if seller_id in self.sellers:
            return {"success": False, "error": "Seller ID already exists."}

        if not name or name.strip() == "":
            return {"success": False, "error": "Seller name cannot be empty."}

        if not isinstance(rating, (int, float)):
            return {"success": False, "error": "Rating must be a number."}

        if rating < 0 or rating > 5:
            return {"success": False, "error": "Rating must be between 0 and 5."}

        self.sellers[seller_id] = {
            "seller_id": seller_id,
            "name": name,
            "rating": float(rating)
        }

        return {"success": True, "message": "Seller added successfully."}

    def update_seller_rating(self, seller_id: str, rating: float) -> dict:
        """
        Change the rating of a seller.

        Args:
            seller_id (str): The unique identifier of the seller.
            rating (float): The new rating to set for the seller.

        Returns:
            dict: {
                "success": True,
                "message": "Seller rating updated"
            }
            or
            {
                "success": False,
                "error": "Reason for failure"
            }

        Constraints:
            - seller_id must exist in the system.
            - rating must be a real (float) number. Negative ratings are not accepted.
        """
        # Seller existence check
        if seller_id not in self.sellers:
            return { "success": False, "error": "Seller ID does not exist" }

        # Minimal validation for rating (disallow negative ratings)
        if not isinstance(rating, (float, int)):
            return { "success": False, "error": "Rating must be a number" }
        if rating < 0:
            return { "success": False, "error": "Rating cannot be negative" }

        # Update the seller's rating
        self.sellers[seller_id]["rating"] = float(rating)
        return { "success": True, "message": "Seller rating updated" }

    def remove_seller(self, seller_id: str) -> dict:
        """
        Remove a seller from the system. All offers belonging to the seller will also be removed.

        Args:
            seller_id (str): The unique ID of the seller to remove.

        Returns:
            dict:
                - On success: {
                    "success": True,
                    "message": "Seller removed (X offers also removed)."
                  }
                - On failure: {
                    "success": False,
                    "error": "Seller does not exist."
                  }

        Constraints:
            - The seller must exist.
            - All offers with seller_id == <seller_id> will be deleted to maintain referential integrity.
        """
        if seller_id not in self.sellers:
            return {"success": False, "error": "Seller does not exist."}

        # Find all offers belonging to this seller
        offers_to_remove = [offer_id for offer_id, offer in self.offers.items() if offer["seller_id"] == seller_id]

        # Remove those offers
        for offer_id in offers_to_remove:
            del self.offers[offer_id]

        # Remove the seller
        del self.sellers[seller_id]

        return {
            "success": True,
            "message": f"Seller removed ({len(offers_to_remove)} offer(s) also removed)."
        }


class EcommerceCatalogOffersSystem(BaseEnv):
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

    def search_products_by_name(self, **kwargs):
        return self._call_inner_tool('search_products_by_name', kwargs)

    def list_offers_for_product(self, **kwargs):
        return self._call_inner_tool('list_offers_for_product', kwargs)

    def list_available_offers_for_product(self, **kwargs):
        return self._call_inner_tool('list_available_offers_for_product', kwargs)

    def get_offer_by_id(self, **kwargs):
        return self._call_inner_tool('get_offer_by_id', kwargs)

    def get_seller_by_id(self, **kwargs):
        return self._call_inner_tool('get_seller_by_id', kwargs)

    def list_sellers(self, **kwargs):
        return self._call_inner_tool('list_sellers', kwargs)

    def list_products_by_category(self, **kwargs):
        return self._call_inner_tool('list_products_by_category', kwargs)

    def get_discount_for_offer(self, **kwargs):
        return self._call_inner_tool('get_discount_for_offer', kwargs)

    def add_product(self, **kwargs):
        return self._call_inner_tool('add_product', kwargs)

    def remove_product(self, **kwargs):
        return self._call_inner_tool('remove_product', kwargs)

    def add_offer(self, **kwargs):
        return self._call_inner_tool('add_offer', kwargs)

    def update_offer_availability(self, **kwargs):
        return self._call_inner_tool('update_offer_availability', kwargs)

    def update_offer_price(self, **kwargs):
        return self._call_inner_tool('update_offer_price', kwargs)

    def update_offer_discount(self, **kwargs):
        return self._call_inner_tool('update_offer_discount', kwargs)

    def remove_offer(self, **kwargs):
        return self._call_inner_tool('remove_offer', kwargs)

    def add_seller(self, **kwargs):
        return self._call_inner_tool('add_seller', kwargs)

    def update_seller_rating(self, **kwargs):
        return self._call_inner_tool('update_seller_rating', kwargs)

    def remove_seller(self, **kwargs):
        return self._call_inner_tool('remove_seller', kwargs)

