# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
from typing import Optional, Dict, List
from typing import Optional, List



# Represents a beverage brand
class BrandInfo(TypedDict):
    brand_id: str
    brand_name: str
    country_of_origin: str

# Represents a beverage category (e.g., gin, vodka)
class CategoryInfo(TypedDict):
    category_id: str
    category_name: str

# Represents an alcoholic beverage product
class ProductInfo(TypedDict):
    product_id: str
    name: str
    brand: str           # reference to brand_id
    category: str        # reference to category_id
    price: float
    volume_ml: int
    alcohol_content_percent: float
    description: str
    origin_country: str
    packaging_type: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Alcoholic beverage e-commerce product catalog environment.
        """

        # Products: {product_id: ProductInfo}
        # State space entity: Product (product_id, name, brand, category, price, volume_ml, alcohol_content_percent, description, origin_country, packaging_type)
        self.products: Dict[str, ProductInfo] = {}

        # Brands: {brand_id: BrandInfo}
        # State space entity: Brand (brand_id, brand_name, country_of_origin)
        self.brands: Dict[str, BrandInfo] = {}

        # Categories: {category_id: CategoryInfo}
        # State space entity: Category (category_id, category_name)
        self.categories: Dict[str, CategoryInfo] = {}

        # Constraints:
        # - Every Product must be associated with exactly one Brand and one Category.
        # - alcohol_content_percent must be in [0, 100].
        # - price must be non-negative.
        # - volume_ml must be positive integer.
        # - Product names must be unique within a given Brand and Category.

    def list_categories(self) -> dict:
        """
        Retrieves all beverage categories in the catalog, including IDs and names.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[CategoryInfo],  # All categories currently in the catalog (can be empty)
            }
        """
        category_list = list(self.categories.values())
        return {
            "success": True,
            "data": category_list
        }

    def list_brands(self) -> dict:
        """
        Retrieve all brands and their countries of origin.

        Returns:
            dict:
                success (bool): True if the operation succeeds.
                data (List[BrandInfo]): A list of all brands with their ids, names, and countries of origin.
            If the catalog contains no brands, data will be an empty list.

        Constraints:
            - No constraints; purely a read-only listing operation.
        """
        brand_list = list(self.brands.values())
        return { "success": True, "data": brand_list }

    def get_category_by_name(self, category_name: str) -> dict:
        """
        Retrieve category details and ID by category name.

        Args:
            category_name (str): The name of the category (e.g., "gin").

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": CategoryInfo  # Dictionary with category_id and category_name
                    }
                - On failure:
                    {
                        "success": False,
                        "error": "Category not found"
                    }

        Constraints:
            - Lookup is case-sensitive by default.
            - If multiple categories have the same name (unexpected), returns the first found.
        """
        for category_info in self.categories.values():
            if category_info["category_name"] == category_name:
                return {"success": True, "data": category_info}
        return {"success": False, "error": "Category not found"}

    def get_brand_by_name(self, brand_name: str) -> dict:
        """
        Retrieve the brand's details (brand_id, brand_name, country_of_origin) using the brand's name.

        Args:
            brand_name (str): The name of the brand to search for.

        Returns:
            dict: 
                - On success:
                    {
                        "success": True,
                        "data": BrandInfo
                    }
                - On failure:
                    {
                        "success": False,
                        "error": "Brand not found"
                    }
        """
        for brand in self.brands.values():
            if brand["brand_name"] == brand_name:
                return {"success": True, "data": brand}
        return {"success": False, "error": "Brand not found"}

    def list_products_by_category(
        self,
        category_id: str = None,
        category_name: str = None
    ) -> dict:
        """
        Retrieve all products belonging to the specified category.
        You can specify the category by its 'category_id' or 'category_name'.
        At least one must be provided.

        Args:
            category_id (str, optional): Unique identifier of the category.
            category_name (str, optional): Name of the category.

        Returns:
            dict:
                - success=True, data=List of ProductInfo dictionaries for this category, or empty if none.
                - success=False, error=str (if category not found or arguments invalid)

        Constraints:
            - Category must exist (by id or name).
            - At least one parameter must be provided.
        """
        if not category_id and not category_name:
            return {
                "success": False,
                "error": "Must provide either category_id or category_name"
            }

        resolved_category_id = None

        if category_id:
            if category_id not in self.categories:
                return {
                    "success": False,
                    "error": f"Category with id '{category_id}' not found"
                }
            resolved_category_id = category_id
        else:
            # Search for category_name (case-insensitive match)
            found = None
            for cat in self.categories.values():
                if cat["category_name"].lower() == category_name.lower():
                    found = cat
                    break
            if not found:
                return {
                    "success": False,
                    "error": f"Category with name '{category_name}' not found"
                }
            resolved_category_id = found["category_id"]

        # Collect all products with matching category
        result = [
            product for product in self.products.values()
            if product["category"] == resolved_category_id
        ]
        return { "success": True, "data": result }


    def list_products_by_brand(self, brand_id: Optional[str] = None, brand_name: Optional[str] = None) -> dict:
        """
        Retrieve all products associated with a specified brand, identified by brand_id or brand_name.

        Args:
            brand_id (str, optional): Unique brand identifier. If provided, takes precedence.
            brand_name (str, optional): Brand name. Used if brand_id not provided or for verification.

        Returns:
            dict:
                - On success: {
                    "success": True,
                    "data": List[ProductInfo],  # May be empty if brand exists but no products
                  }
                - On failure: {
                    "success": False,
                    "error": str
                  }

        Constraints:
            - Brand must exist in catalog (match brand_id or brand_name).
            - If both brand_id and brand_name are given, must refer to the same brand.
            - At least one of brand_id or brand_name must be provided.
        """
        # Check for at least one identifier
        if not brand_id and not brand_name:
            return {"success": False, "error": "Must provide either brand_id or brand_name."}

        # Resolve brand_id
        resolved_brand_id = None
        if brand_id is not None:
            if brand_id not in self.brands:
                return {"success": False, "error": f"Brand with id '{brand_id}' does not exist."}
            resolved_brand_id = brand_id
            # If both provided, check name matches
            if brand_name is not None:
                if self.brands[brand_id]['brand_name'].lower() != brand_name.lower():
                    return {"success": False, "error": "brand_id and brand_name refer to different brands."}
        elif brand_name is not None:
            # Lookup by brand_name (case-insensitive)
            found = None
            for b_id, b_info in self.brands.items():
                if b_info['brand_name'].lower() == brand_name.lower():
                    found = b_id
                    break
            if found is None:
                return {"success": False, "error": f"Brand with name '{brand_name}' does not exist."}
            resolved_brand_id = found

        # Gather products for resolved_brand_id
        data = [
            prod for prod in self.products.values()
            if prod['brand'] == resolved_brand_id
        ]
        return {"success": True, "data": data}


    def search_products(
        self,
        keyword: Optional[str] = None,
        brand_id: Optional[str] = None,
        category_id: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_alcohol: Optional[float] = None,
        max_alcohol: Optional[float] = None,
        min_volume: Optional[int] = None,
        max_volume: Optional[int] = None,
        origin_country: Optional[str] = None,
        packaging_type: Optional[str] = None
    ) -> dict:
        """
        Search for products by keyword (matching name or description, case-insensitive),
        with optional filtering by brand, category, price, volume, alcohol content, origin country,
        and packaging type.

        Args:
            keyword (Optional[str]): Keyword to search for in product name/description.
            brand_id (Optional[str]): Restrict results to this brand_id.
            category_id (Optional[str]): Restrict results to this category_id.
            min_price (Optional[float]): Minimum price filter (inclusive).
            max_price (Optional[float]): Maximum price filter (inclusive).
            min_alcohol (Optional[float]): Minimum alcohol content filter (inclusive).
            max_alcohol (Optional[float]): Maximum alcohol content filter (inclusive).
            min_volume (Optional[int]): Minimum volume (ml) filter (inclusive).
            max_volume (Optional[int]): Maximum volume (ml) filter (inclusive).
            origin_country (Optional[str]): Filter by origin country (exact match, case-insensitive).
            packaging_type (Optional[str]): Filter by packaging type (exact match, case-insensitive).

        Returns:
            dict: {
                "success": True,
                "data": List[ProductInfo],  # possibly empty
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - If brand_id or category_id are provided, they must exist.
            - All numeric filters (min/max) must be valid if provided.
            - Keyword, if provided, matches substring-insensitively in name or description.
        """

        # Brand existence check
        if brand_id is not None and brand_id not in self.brands:
            return {"success": False, "error": f"Brand '{brand_id}' does not exist"}

        # Category existence check
        if category_id is not None and category_id not in self.categories:
            return {"success": False, "error": f"Category '{category_id}' does not exist"}

        results: List[ProductInfo] = []
        keyword_lower = keyword.lower() if keyword and isinstance(keyword, str) else None

        for product in self.products.values():
            # Keyword search
            if keyword_lower:
                name_match = keyword_lower in product['name'].lower()
                desc_match = keyword_lower in product['description'].lower()
                if not (name_match or desc_match):
                    continue

            # Brand filter
            if brand_id is not None and product["brand"] != brand_id:
                continue

            # Category filter
            if category_id is not None and product["category"] != category_id:
                continue

            # Price
            if min_price is not None and product["price"] < min_price:
                continue
            if max_price is not None and product["price"] > max_price:
                continue

            # Alcohol content
            if min_alcohol is not None and product["alcohol_content_percent"] < min_alcohol:
                continue
            if max_alcohol is not None and product["alcohol_content_percent"] > max_alcohol:
                continue

            # Volume
            if min_volume is not None and product["volume_ml"] < min_volume:
                continue
            if max_volume is not None and product["volume_ml"] > max_volume:
                continue

            # Origin country
            if origin_country is not None and product["origin_country"].lower() != origin_country.lower():
                continue

            # Packaging type
            if packaging_type is not None and product["packaging_type"].lower() != packaging_type.lower():
                continue

            results.append(product)

        return {"success": True, "data": results}

    def get_product_details(self, product_id: str) -> dict:
        """
        Retrieve the full details of a product by its product_id.

        Args:
            product_id (str): The unique identifier for the product.

        Returns:
            dict: {
                "success": True,
                "data": ProductInfo  # complete details about the product
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., product not found
            }

        Constraints:
            - Product must exist by id.
        """
        product = self.products.get(product_id)
        if not product:
            return { "success": False, "error": "Product not found" }
        return { "success": True, "data": product }

    def filter_products_by_attribute(
        self,
        min_price: float = None,
        max_price: float = None,
        min_volume_ml: int = None,
        max_volume_ml: int = None,
        min_alcohol_content_percent: float = None,
        max_alcohol_content_percent: float = None
    ) -> dict:
        """
        Filter products by price range, volume (ml) range, and/or alcohol content percent range.

        Args:
            min_price (float, optional): Minimum price, inclusive.
            max_price (float, optional): Maximum price, inclusive.
            min_volume_ml (int, optional): Minimum volume in ml, inclusive.
            max_volume_ml (int, optional): Maximum volume in ml, inclusive.
            min_alcohol_content_percent (float, optional): Minimum alcohol content percent, inclusive.
            max_alcohol_content_percent (float, optional): Maximum alcohol content percent, inclusive.

        Returns:
            dict: {
                "success": True,
                "data": List[ProductInfo],  # products matching the filters
            }
            or
            {
                "success": False,
                "error": str
            }

        Edge cases:
            - If min_price > max_price, etc., returns error.
            - If all filters are None, returns all products.
        """
        # Validate filter ranges
        if min_price is not None and max_price is not None and min_price > max_price:
            return {"success": False, "error": "min_price cannot be greater than max_price"}
        if min_volume_ml is not None and max_volume_ml is not None and min_volume_ml > max_volume_ml:
            return {"success": False, "error": "min_volume_ml cannot be greater than max_volume_ml"}
        if (min_alcohol_content_percent is not None and max_alcohol_content_percent is not None and
                min_alcohol_content_percent > max_alcohol_content_percent):
            return {"success": False, "error": "min_alcohol_content_percent cannot be greater than max_alcohol_content_percent"}
    
        result = []
        for product in self.products.values():
            # Price filter
            if min_price is not None and product["price"] < min_price:
                continue
            if max_price is not None and product["price"] > max_price:
                continue
            # Volume filter
            if min_volume_ml is not None and product["volume_ml"] < min_volume_ml:
                continue
            if max_volume_ml is not None and product["volume_ml"] > max_volume_ml:
                continue
            # Alcohol content percent filter
            if min_alcohol_content_percent is not None and product["alcohol_content_percent"] < min_alcohol_content_percent:
                continue
            if max_alcohol_content_percent is not None and product["alcohol_content_percent"] > max_alcohol_content_percent:
                continue
            # If passed all filters, add
            result.append(product)
        return {"success": True, "data": result}

    def get_product_by_name_brand_category(
        self, name: str, brand_id: str, category_id: str
    ) -> dict:
        """
        Retrieve a product by its name, brand, and category (all must match).

        Args:
            name (str): The product name.
            brand_id (str): The identifier of the brand.
            category_id (str): The identifier of the category.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": ProductInfo
                    }
                - On failure (not found or invalid input):
                    {
                        "success": False,
                        "error": "Product not found" | "Brand or category does not exist"
                    }

        Constraints:
            - Brand and category must exist.
            - Product names are unique within brand and category; at most one match.
        """
        if brand_id not in self.brands or category_id not in self.categories:
            return { "success": False, "error": "Brand or category does not exist" }

        for p in self.products.values():
            if (
                p["name"] == name
                and p["brand"] == brand_id
                and p["category"] == category_id
            ):
                return { "success": True, "data": p }

        return { "success": False, "error": "Product not found" }

    def add_product(
        self,
        product_id: str,
        name: str,
        brand: str,
        category: str,
        price: float,
        volume_ml: int,
        alcohol_content_percent: float,
        description: str,
        origin_country: str,
        packaging_type: str
    ) -> dict:
        """
        Add a new product to the catalog, enforcing all catalog constraints.

        Args:
            product_id (str): Unique product ID.
            name (str): Product name (must be unique within brand+category).
            brand (str): Brand ID (must exist).
            category (str): Category ID (must exist).
            price (float): Non-negative price.
            volume_ml (int): Volume in ml, must be positive.
            alcohol_content_percent (float): Alcohol content % (0-100 inclusive).
            description (str): Product description.
            origin_country (str): Country of origin for the product.
            packaging_type (str): Packaging descriptor.

        Returns:
            dict: {
                "success": True, "message": "Product added: <product_id>"
            } or {
                "success": False, "error": "<reason>"
            }
        Constraints:
            - The referenced brand/category must exist.
            - alcohol_content_percent must be in [0,100].
            - price >= 0.
            - volume_ml > 0.
            - No duplicate (name, brand, category) among products.
        """

        # 1. Validate unique product_id and (name, brand, category) tuple
        if product_id in self.products:
            return {"success": False, "error": "Product ID already exists"}
        for prod in self.products.values():
            if (
                prod["name"] == name and
                prod["brand"] == brand and
                prod["category"] == category
            ):
                return {"success": False, "error": "Product name already exists for this brand and category"}
        # 2. Validate brand and category reference
        if brand not in self.brands:
            return {"success": False, "error": "Referenced brand does not exist"}
        if category not in self.categories:
            return {"success": False, "error": "Referenced category does not exist"}
        # 3. Validate attribute constraints
        if not isinstance(price, (int, float)) or price < 0:
            return {"success": False, "error": "Invalid price: must be non-negative"}
        if not isinstance(volume_ml, int) or volume_ml <= 0:
            return {"success": False, "error": "Invalid volume_ml: must be positive integer"}
        if (
            not isinstance(alcohol_content_percent, (int, float)) or
            alcohol_content_percent < 0 or
            alcohol_content_percent > 100
        ):
            return {"success": False, "error": "Invalid alcohol_content_percent: must be in [0,100]"}
        # All validations passed. Add product.
        self.products[product_id] = {
            "product_id": product_id,
            "name": name,
            "brand": brand,
            "category": category,
            "price": float(price),
            "volume_ml": int(volume_ml),
            "alcohol_content_percent": float(alcohol_content_percent),
            "description": description,
            "origin_country": origin_country,
            "packaging_type": packaging_type,
        }
        return {"success": True, "message": f"Product added: {product_id}"}

    def update_product(
        self,
        product_id: str,
        name: str = None,
        brand: str = None,
        category: str = None,
        price: float = None,
        volume_ml: int = None,
        alcohol_content_percent: float = None,
        description: str = None,
        origin_country: str = None,
        packaging_type: str = None
    ) -> dict:
        """
        Update an existing product's details, enforcing catalog constraints.

        Args:
            product_id (str): ID of the product to update.
            name (str, optional): New name for the product (must be unique within the brand and category).
            brand (str, optional): New brand_id (must exist in catalog).
            category (str, optional): New category_id (must exist in catalog).
            price (float, optional): New price (must be non-negative).
            volume_ml (int, optional): New volume in ml (must be positive integer).
            alcohol_content_percent (float, optional): New alcohol content (must be in [0, 100]).
            description (str, optional): New description.
            origin_country (str, optional): New origin country.
            packaging_type (str, optional): New packaging type.

        Returns:
            dict:
                On success: { "success": True, "message": "Product updated successfully." }
                On failure: { "success": False, "error": "reason" }

        Constraints:
            - product_id must exist.
            - Product name must be unique within (brand, category).
            - Brand and category must exist.
            - alcohol_content_percent in [0, 100].
            - price >= 0.
            - volume_ml > 0.
        """
        # -- Check that the product exists --
        if product_id not in self.products:
            return { "success": False, "error": "Product not found." }

        current_product = self.products[product_id]
    
        # Prepare proposed new fields
        new_name = name if name is not None else current_product['name']
        new_brand = brand if brand is not None else current_product['brand']
        new_category = category if category is not None else current_product['category']
        new_price = price if price is not None else current_product['price']
        new_volume_ml = volume_ml if volume_ml is not None else current_product['volume_ml']
        new_alcohol_content_percent = alcohol_content_percent if alcohol_content_percent is not None else current_product['alcohol_content_percent']
        new_description = description if description is not None else current_product['description']
        new_origin_country = origin_country if origin_country is not None else current_product['origin_country']
        new_packaging_type = packaging_type if packaging_type is not None else current_product['packaging_type']

        # -- Enforce constraints --

        # Check new brand exists
        if new_brand not in self.brands:
            return { "success": False, "error": "Specified brand does not exist." }

        # Check new category exists
        if new_category not in self.categories:
            return { "success": False, "error": "Specified category does not exist." }

        # alcohol_content_percent in [0, 100]
        if not (0 <= new_alcohol_content_percent <= 100):
            return { "success": False, "error": "Alcohol content percent must be between 0 and 100." }

        # price >= 0
        if new_price < 0:
            return { "success": False, "error": "Price must be non-negative." }

        # volume_ml > 0 and integer
        if not (isinstance(new_volume_ml, int) and new_volume_ml > 0):
            return { "success": False, "error": "Volume must be a positive integer." }

        # Name must be unique within (brand, category)
        for prod in self.products.values():
            if prod['product_id'] != product_id and \
               prod['name'] == new_name and \
               prod['brand'] == new_brand and \
               prod['category'] == new_category:
                return { "success": False, "error": "Product name must be unique within the brand and category." }

        # All constraints passed, do the update
        self.products[product_id] = {
            "product_id": product_id,
            "name": new_name,
            "brand": new_brand,
            "category": new_category,
            "price": new_price,
            "volume_ml": new_volume_ml,
            "alcohol_content_percent": new_alcohol_content_percent,
            "description": new_description,
            "origin_country": new_origin_country,
            "packaging_type": new_packaging_type
        }

        return { "success": True, "message": "Product updated successfully." }

    def delete_product(self, product_id: str) -> dict:
        """
        Remove a product from the catalog by its product_id.

        Args:
            product_id (str): The unique identifier of the product to remove.

        Returns:
            dict: 
              On success:
                { "success": True, "message": "Product <product_id> deleted successfully." }
              On error:
                { "success": False, "error": "Product not found." }

        Constraints:
            - Fails if the product_id does not exist in the catalog.
            - Removes only the Product record; does not affect Brand or Category entities.
        """
        if product_id not in self.products:
            return { "success": False, "error": "Product not found." }

        del self.products[product_id]
        return { "success": True, "message": f"Product {product_id} deleted successfully." }

    def add_brand(self, brand_id: str, brand_name: str, country_of_origin: str) -> dict:
        """
        Add a new brand to the product catalog.

        Args:
            brand_id (str): Unique brand identifier.
            brand_name (str): Brand's human-readable name (must be unique, case-insensitive).
            country_of_origin (str): The country where the brand originates.

        Returns:
            dict: On success: { "success": True, "message": "Brand <brand_id> added successfully." }
                  On failure: { "success": False, "error": <reason> }

        Constraints:
            - brand_id must be unique.
            - brand_name must be unique (case-insensitive) among all brands.
            - All parameters must be non-empty strings.
        """
        if not brand_id or not brand_name or not country_of_origin:
            return {"success": False, "error": "All parameters (brand_id, brand_name, country_of_origin) are required."}

        if brand_id in self.brands:
            return {"success": False, "error": f"Brand ID '{brand_id}' already exists."}

        for existing in self.brands.values():
            if existing["brand_name"].strip().lower() == brand_name.strip().lower():
                return {"success": False, "error": f"Brand name '{brand_name}' already exists."}

        brand_info = {
            "brand_id": brand_id,
            "brand_name": brand_name,
            "country_of_origin": country_of_origin
        }
        self.brands[brand_id] = brand_info
        return {"success": True, "message": f"Brand {brand_id} added successfully."}

    def update_brand(self, brand_id: str, brand_name: str = None, country_of_origin: str = None) -> dict:
        """
        Update details of an existing brand.

        Args:
            brand_id (str): Unique identifier of the brand to update.
            brand_name (str, optional): New brand name. If None, do not update.
            country_of_origin (str, optional): New country of origin. If None, do not update.

        Returns:
            dict:
                On success: { "success": True, "message": "Brand updated successfully" }
                On failure: { "success": False, "error": "<error_reason>" }

        Constraints:
            - Brand with the given brand_id must exist.
            - At least one update field must be provided.
        """
        if brand_id not in self.brands:
            return { "success": False, "error": "Brand with the given ID does not exist" }

        if brand_name is None and country_of_origin is None:
            return { "success": False, "error": "No update fields provided" }

        if brand_name is not None:
            self.brands[brand_id]["brand_name"] = brand_name
        if country_of_origin is not None:
            self.brands[brand_id]["country_of_origin"] = country_of_origin

        return { "success": True, "message": "Brand updated successfully" }

    def delete_brand(self, brand_id: str) -> dict:
        """
        Remove a brand from the catalog.
        Fails if there are any products referencing the brand (to avoid orphaned products).

        Args:
            brand_id (str): The ID of the brand to be deleted.

        Returns:
            dict: {
                "success": True,
                "message": str  # Brand deleted successfully message
            }
            or
            {
                "success": False,
                "error": str  # Detailed error: brand doesn't exist or orphaned product(s) found
            }

        Constraints:
            - Can only delete a brand if no products reference it.
            - Orphaned products are NOT allowed.
        """
        if brand_id not in self.brands:
            return {"success": False, "error": f"Brand '{brand_id}' does not exist."}

        # Find any products referencing this brand
        orphaned_products = [
            prod["product_id"]
            for prod in self.products.values()
            if prod["brand"] == brand_id
        ]
        if orphaned_products:
            return {
                "success": False,
                "error": (
                    f"Cannot delete brand '{brand_id}': "
                    f"referenced by product(s) {orphaned_products}."
                )
            }

        # Safe to delete the brand
        del self.brands[brand_id]
        return {
            "success": True,
            "message": f"Brand '{brand_id}' deleted successfully."
        }

    def add_category(self, category_id: str, category_name: str) -> dict:
        """
        Add a new beverage category to the catalog.

        Args:
            category_id (str): Unique identifier for the category.
            category_name (str): Name of the beverage category.

        Returns:
            dict:
                - On success: {"success": True, "message": "Category <category_name> added successfully."}
                - On failure: {"success": False, "error": "<reason>"}

        Constraints:
            - category_id must be unique in the catalog.
            - (Recommended) category_name should be unique for clarity.
        """
        if not category_id or not category_name:
            return {"success": False, "error": "Category ID and name must be provided."}

        if category_id in self.categories:
            return {"success": False, "error": "Category ID already exists."}

        # Optional uniqueness on category_name (no hard rule, but avoids confusion)
        for cat in self.categories.values():
            if cat["category_name"].lower() == category_name.lower():
                return {"success": False, "error": "Category name already exists."}

        self.categories[category_id] = {
            "category_id": category_id,
            "category_name": category_name
        }

        return {
            "success": True,
            "message": f"Category {category_name} added successfully."
        }

    def update_category(self, category_id: str, category_name: str = None) -> dict:
        """
        Update details of an existing category in the product catalog.

        Args:
            category_id (str): The unique ID of the category to update.
            category_name (str, optional): The new name for the category.

        Returns:
            dict:
                { "success": True, "message": "Category updated successfully." }
                or
                { "success": False, "error": "<reason>" }

        Constraints:
            - The category_id must exist.
            - If category_name is provided, it should not duplicate another category's name.
        """
        # Check if the category exists
        if category_id not in self.categories:
            return {"success": False, "error": "Category does not exist."}
    
        # If new name is provided, check for name uniqueness
        if category_name is not None:
            for cid, cat in self.categories.items():
                if cid != category_id and cat["category_name"].strip().lower() == category_name.strip().lower():
                    return {"success": False, "error": "Category name already exists for another category."}
            # Update category name
            self.categories[category_id]["category_name"] = category_name.strip()
    
        # Success (whether changes made or not)
        return {"success": True, "message": "Category updated successfully."}

    def delete_category(self, category_id: str) -> dict:
        """
        Remove a category from the catalog.
        Also removes all products associated with this category to prevent orphans.

        Args:
            category_id (str): The ID of the category to delete.

        Returns:
            dict:
                Success: {
                    "success": True,
                    "message": "Category <category_id> deleted"
                }
                Failure: {
                    "success": False,
                    "error": <reason>
                }

        Constraints:
            - The category must exist.
            - All products associated with this category will also be deleted to avoid orphaned products.
        """
        if category_id not in self.categories:
            return { "success": False, "error": "Category does not exist" }

        # Remove all products in this category to avoid orphaning
        to_remove = [pid for pid, info in self.products.items() if info["category"] == category_id]
        for pid in to_remove:
            del self.products[pid]

        # Delete the category itself
        del self.categories[category_id]

        return {
            "success": True,
            "message": f"Category {category_id} deleted"
        }


class AlcoholicBeverageProductCatalog(BaseEnv):
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

    def list_categories(self, **kwargs):
        return self._call_inner_tool('list_categories', kwargs)

    def list_brands(self, **kwargs):
        return self._call_inner_tool('list_brands', kwargs)

    def get_category_by_name(self, **kwargs):
        return self._call_inner_tool('get_category_by_name', kwargs)

    def get_brand_by_name(self, **kwargs):
        return self._call_inner_tool('get_brand_by_name', kwargs)

    def list_products_by_category(self, **kwargs):
        return self._call_inner_tool('list_products_by_category', kwargs)

    def list_products_by_brand(self, **kwargs):
        return self._call_inner_tool('list_products_by_brand', kwargs)

    def search_products(self, **kwargs):
        return self._call_inner_tool('search_products', kwargs)

    def get_product_details(self, **kwargs):
        return self._call_inner_tool('get_product_details', kwargs)

    def filter_products_by_attribute(self, **kwargs):
        return self._call_inner_tool('filter_products_by_attribute', kwargs)

    def get_product_by_name_brand_category(self, **kwargs):
        return self._call_inner_tool('get_product_by_name_brand_category', kwargs)

    def add_product(self, **kwargs):
        return self._call_inner_tool('add_product', kwargs)

    def update_product(self, **kwargs):
        return self._call_inner_tool('update_product', kwargs)

    def delete_product(self, **kwargs):
        return self._call_inner_tool('delete_product', kwargs)

    def add_brand(self, **kwargs):
        return self._call_inner_tool('add_brand', kwargs)

    def update_brand(self, **kwargs):
        return self._call_inner_tool('update_brand', kwargs)

    def delete_brand(self, **kwargs):
        return self._call_inner_tool('delete_brand', kwargs)

    def add_category(self, **kwargs):
        return self._call_inner_tool('add_category', kwargs)

    def update_category(self, **kwargs):
        return self._call_inner_tool('update_category', kwargs)

    def delete_category(self, **kwargs):
        return self._call_inner_tool('delete_category', kwargs)

