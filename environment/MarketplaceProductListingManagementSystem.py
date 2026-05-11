# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, Optional, TypedDict
import uuid
from typing import Dict, Any



class ProductCategoryInfo(TypedDict):
    category_id: str
    name: str
    parent_category_id: Optional[str]

class AttributeSchemaInfo(TypedDict):
    attribute_id: str
    category_id: str
    name: str
    required: bool
    allowed_values: List[str]

class AttributeValueInfo(TypedDict):
    attribute_id: str
    value: str
    display_name: str

class SellerListingInfo(TypedDict):
    listing_id: str
    seller_id: str
    category_id: str
    attribute_values: Dict[str, str]  # mapping attribute_id → value
    status: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for managing marketplace product listings.
        """

        # Product Categories: {category_id: ProductCategoryInfo}
        # Maps all available product categories.
        self.product_categories: Dict[str, ProductCategoryInfo] = {}

        # Attribute Schemas: {attribute_id: AttributeSchemaInfo}
        # Sets of attributes per category, their requirements, and allowed values.
        self.attribute_schemas: Dict[str, AttributeSchemaInfo] = {}

        # Attribute Values: {attribute_id: List[AttributeValueInfo]}
        # Allowed values for each attribute.
        self.attribute_values: Dict[str, List[AttributeValueInfo]] = {}

        # Seller Listings: {listing_id: SellerListingInfo}
        # Seller-created listings with chosen attributes and values.
        self.seller_listings: Dict[str, SellerListingInfo] = {}

        # Constraint Annotations:
        # - Only categories present in ProductCategory can be selected for listings.
        # - Attributes for a listing must conform to the schema (required attributes must be provided; optional attributes may be omitted).
        # - Attribute values for each attribute must be selected from the permissible set defined in AttributeValue.
        # - Listings cannot be created or published unless all schema and category constraints are satisfied.

    def list_product_categories(self) -> dict:
        """
        Retrieve the full list of available product categories, including category id, name, and parent hierarchy.

        Returns:
            dict: {
                "success": True,
                "data": List[ProductCategoryInfo],  # List of all category info dicts (possibly empty)
            }

        Constraints:
            - None; all categories present in self.product_categories are returned.
        """
        result = list(self.product_categories.values())
        return {
            "success": True,
            "data": result
        }

    def get_category_by_id(self, category_id: str) -> dict:
        """
        Get details for a specific product category by its category_id.

        Args:
            category_id (str): Unique identifier of the category to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": ProductCategoryInfo  # Category info, including parent_category_id
            }
            or
            {
                "success": False,
                "error": str  # E.g., "Category not found"
            }

        Constraints:
            - The category_id must exist in the product_categories mapping.
        """
        if category_id not in self.product_categories:
            return {"success": False, "error": "Category not found"}

        category_info = self.product_categories[category_id]
        return {"success": True, "data": category_info}

    def list_category_attribute_schemas(self, category_id: str) -> dict:
        """
        Retrieve all attribute schema definitions for a specific product category.

        Args:
            category_id (str): ID of the product category.

        Returns:
            dict: 
              - If the category exists: {
                    "success": True,
                    "data": List[AttributeSchemaInfo]
                }
              - If the category does not exist: {
                    "success": False,
                    "error": "Category does not exist"
                }

        Constraints:
            - category_id must be present in self.product_categories.
        """
        if category_id not in self.product_categories:
            return { "success": False, "error": "Category does not exist" }

        result = [
            schema for schema in self.attribute_schemas.values()
            if schema["category_id"] == category_id
        ]

        return { "success": True, "data": result }

    def get_attribute_schema_by_id(self, attribute_id: str) -> dict:
        """
        Return the attribute schema details for the specified attribute_id.

        Args:
            attribute_id (str): The unique ID of the attribute schema.

        Returns:
            dict: {
                "success": True,
                "data": AttributeSchemaInfo,  # All details about the attribute schema
            }
            or
            {
                "success": False,
                "error": str  # Reason ('Attribute schema not found')
            }

        Constraints:
            - The attribute_id must exist within the attribute_schemas.
        """
        attribute_schema = self.attribute_schemas.get(attribute_id)
        if attribute_schema is None:
            return {
                "success": False,
                "error": "Attribute schema not found"
            }
        return {
            "success": True,
            "data": attribute_schema
        }

    def list_attribute_values(self, attribute_id: str) -> dict:
        """
        Retrieve the allowed values and their display names for a given attribute_id.

        Args:
            attribute_id (str): The identifier for the attribute whose values are to be retrieved.

        Returns:
            dict:
              - If attribute_id exists:
                  { "success": True, "data": List[AttributeValueInfo] }
              - If attribute_id does not exist:
                  { "success": False, "error": "Attribute ID not found" }

        Constraints:
            - The attribute_id must exist in the registered attribute schemas.
        """
        if attribute_id not in self.attribute_schemas:
            return { "success": False, "error": "Attribute ID not found" }
        # Even if there are no values defined for this attribute, return an empty list
        data = self.attribute_values.get(attribute_id, [])
        return { "success": True, "data": data }

    def list_seller_listings(self, seller_id: str) -> dict:
        """
        List all existing listings (draft or published) for a given seller.

        Args:
            seller_id (str): The unique identifier for the seller.

        Returns:
            dict: {
                "success": True,
                "data": List[SellerListingInfo]  # all listings for the seller (possibly empty)
            }
            or
            {
                "success": False,
                "error": str  # if seller_id invalid
            }

        Constraints:
            - No additional constraints. Returns all listings belonging to seller, regardless of status.
        """
        if not seller_id or not isinstance(seller_id, str):
            return {"success": False, "error": "Invalid seller_id"}

        result = [
            listing for listing in self.seller_listings.values()
            if listing["seller_id"] == seller_id
        ]

        return {"success": True, "data": result}

    def get_listing_by_id(self, listing_id: str) -> dict:
        """
        Retrieve the details (including the complete attribute-value mapping) for a specific listing.

        Args:
            listing_id (str): Unique identifier of the seller listing to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": SellerListingInfo  # All details for the listing, including attribute_values mapping
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., listing does not exist)
            }

        Constraints:
            - Listing must exist.
        """
        listing = self.seller_listings.get(listing_id)
        if not listing:
            return { "success": False, "error": "Listing does not exist" }

        return { "success": True, "data": listing }


    def create_listing(
        self,
        seller_id: str,
        category_id: str,
        attribute_values: Dict[str, str]
    ) -> dict:
        """
        Create a new seller listing by validating and adding it to the system.

        Args:
            seller_id (str): Seller's identifier.
            category_id (str): Product category ID, must exist in product_categories.
            attribute_values (dict): Mapping attribute_id → value (str), must satisfy required attributes and allowed values.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "message": "Listing created",
                        "listing_id": str
                    }
                - On error:
                    {
                        "success": False,
                        "error": str  # description of the error
                    }

        Constraints:
            - Only categories present in ProductCategory can be selected.
            - Attributes must conform to schema (required/optional).
            - Provided values for each attribute must be selected from the permissible set (AttributeValue).
            - No unknown/invalid attribute_ids.
            - Listing is created in 'draft' state by default.
        """
        # Check category existence
        if category_id not in self.product_categories:
            return {"success": False, "error": "Category does not exist"}

        # 1. Get all attribute schemas for this category
        attributes_for_category = [
            attr for attr in self.attribute_schemas.values()
            if attr["category_id"] == category_id
        ]
        schema_attr_ids = set(attr["attribute_id"] for attr in attributes_for_category)

        # 2. Check that all attributes provided are defined in schema
        for aid in attribute_values.keys():
            if aid not in schema_attr_ids:
                return {"success": False, "error": f"Attribute '{aid}' not valid for selected category"}

        # 3. Check required attributes
        missing_required = [
            attr["attribute_id"]
            for attr in attributes_for_category
            if attr["required"] and attr["attribute_id"] not in attribute_values
        ]
        if missing_required:
            return {
                "success": False,
                "error": f"Missing required attributes: {', '.join(missing_required)}"
            }

        # 4. Check all attribute values provided are permitted (if attribute_values non-empty)
        for aid, val in attribute_values.items():
            allowed_vals = set(
                [av["value"] for av in self.attribute_values.get(aid, [])]
            )
            if val not in allowed_vals:
                return {
                    "success": False,
                    "error": f"Value '{val}' not allowed for attribute '{aid}'"
                }

        # 5. Generate a unique listing id (UUID)
        new_listing_id = str(uuid.uuid4())

        # 6. Create listing record with status 'draft' (default)
        listing: SellerListingInfo = {
            "listing_id": new_listing_id,
            "seller_id": seller_id,
            "category_id": category_id,
            "attribute_values": dict(attribute_values),  # copy for safety
            "status": "draft"
        }
        self.seller_listings[new_listing_id] = listing

        return {
            "success": True,
            "message": "Listing created",
            "listing_id": new_listing_id
        }

    def update_listing_attributes(self, listing_id: str, attribute_values: Dict[str, str]) -> dict:
        """
        Update the attribute values for an existing seller listing, ensuring:
        - The listing exists.
        - The listing's category exists.
        - Only attributes defined for the category are updated.
        - All required attributes for the category are provided and set to allowed values.
        - No extra attributes outside the schema.
        - All provided attribute values conform to their allowed values.

        Args:
            listing_id (str): The ID of the listing to update.
            attribute_values (Dict[str, str]): Mapping of attribute_id → value for the listing.

        Returns:
            dict: {
                "success": True,
                "message": "Listing attributes updated successfully."
            }
            or
            {
                "success": False,
                "error": str
            }
        """
        # 1. Check if listing exists
        if listing_id not in self.seller_listings:
            return { "success": False, "error": "Listing does not exist." }

        listing = self.seller_listings[listing_id]
        category_id = listing["category_id"]

        # 2. Check if category exists
        if category_id not in self.product_categories:
            return { "success": False, "error": "Listing's category does not exist." }

        # 3. Gather all attribute schemas for the category
        # attribute_schemas: {attribute_id: AttributeSchemaInfo}
        category_schema_attrs = [
            attr for attr in self.attribute_schemas.values()
            if attr["category_id"] == category_id
        ]
        schema_attr_ids = set(attr["attribute_id"] for attr in category_schema_attrs)

        # 4. Check that submitted attributes are all in the schema for the category
        for submitted_attr_id in attribute_values:
            if submitted_attr_id not in schema_attr_ids:
                return {
                    "success": False,
                    "error": f"Attribute ID '{submitted_attr_id}' is not defined for this listing's category."
                }

        # 5. Check required attributes are present
        for attr in category_schema_attrs:
            if attr["required"]:
                if attr["attribute_id"] not in attribute_values:
                    return {
                        "success": False,
                        "error": f"Missing required attribute: '{attr['name']}' (ID: {attr['attribute_id']})"
                    }

        # 6. For each provided attribute, check value is allowed
        for attr_id, value in attribute_values.items():
            allowed_values = set([val["value"] for val in self.attribute_values.get(attr_id, [])])
            if value not in allowed_values:
                return {
                    "success": False,
                    "error": f"Value '{value}' is not allowed for attribute ID '{attr_id}'."
                }

        # 7. Optional: Ensure that no extra attributes outside schema are left after update (already checked above)

        # 8. Update the listing's attribute_values
        listing["attribute_values"] = attribute_values.copy()
        self.seller_listings[listing_id] = listing

        return {
            "success": True,
            "message": "Listing attributes updated successfully."
        }

    def validate_listing(self, listing_id: str) -> dict:
        """
        Validate a seller listing for schema compliance:
        - Listing must exist.
        - Listing's category must be valid.
        - All required attributes from schema for the category must be present.
        - No extra attributes (only those in the category's schema).
        - Each attribute value must be in its allowed set.

        Args:
            listing_id (str): The seller listing to validate.

        Returns:
            dict: {
                "success": True,
                "message": "Listing is valid."
            }
            or
            {
                "success": False,
                "error": "<summary string>",
                "details": {
                    ... error detail fields ...
                }
            }
        """
        # 1. Check if listing exists
        listing = self.seller_listings.get(listing_id)
        if not listing:
            return {
                "success": False,
                "error": f"Listing with id '{listing_id}' does not exist."
            }

        category_id = listing.get("category_id")
        attr_values = listing.get("attribute_values", {})

        # 2. Check if category exists
        if category_id not in self.product_categories:
            return {
                "success": False,
                "error": f"Category with id '{category_id}' for this listing does not exist."
            }

        # 3. Gather all attribute schemas for this category
        schemas = [
            schema for schema in self.attribute_schemas.values()
            if schema["category_id"] == category_id
        ]
        schema_attr_ids = set(schema["attribute_id"] for schema in schemas)

        # 4. Check for required attributes, missing required
        required_attr_ids = set(schema["attribute_id"] for schema in schemas if schema.get("required", False))
        supplied_attr_ids = set(attr_values.keys())
        missing_required = sorted(list(required_attr_ids - supplied_attr_ids))

        # 5. Check for extra attributes (those not in schema for this category)
        extra_attributes = sorted(list(supplied_attr_ids - schema_attr_ids))

        # 6. For each supplied attribute, check its value is allowed
        invalid_value_attrs = []
        for attr_id, value in attr_values.items():
            if attr_id not in schema_attr_ids:
                continue  # already handled as extra_attributes
            # Allowed values: Use attribute_values structure, fall back to schema's allowed_values
            allowed_vals_set = set()
            if attr_id in self.attribute_values:
                allowed_vals_set = set([v["value"] for v in self.attribute_values[attr_id]])
            elif attr_id in self.attribute_schemas:
                allowed_vals_set = set(self.attribute_schemas[attr_id].get("allowed_values", []))
            if value not in allowed_vals_set:
                invalid_value_attrs.append({
                    "attribute_id": attr_id,
                    "supplied_value": value,
                    "allowed_values": list(allowed_vals_set)
                })

        errors_detected = any([
            missing_required,
            extra_attributes,
            invalid_value_attrs,
        ])

        if errors_detected:
            error_list = []
            if missing_required:
                error_list.append(f"Missing required attributes: {missing_required}")
            if extra_attributes:
                error_list.append(f"Extra attributes: {extra_attributes}")
            if invalid_value_attrs:
                error_list.append(
                    f"Invalid values for attributes: {[x['attribute_id'] for x in invalid_value_attrs]}"
                )
            return {
                "success": False,
                "error": "; ".join(error_list),
                "details": {
                    "missing_required": missing_required,
                    "extra_attributes": extra_attributes,
                    "invalid_value_attributes": invalid_value_attrs
                }
            }

        return {
            "success": True,
            "message": "Listing is valid."
        }

    def publish_listing(self, listing_id: str) -> dict:
        """
        Publishes a validated listing by setting its status to 'published', making it available in the marketplace.

        Args:
            listing_id (str): The unique identifier for the seller's listing to publish.

        Returns:
            dict: {
                "success": True,
                "message": "Listing <listing_id> has been published."
            }
            or
            {
                "success": False,
                "error": <description of the error>
            }

        Constraints:
            - The listing must exist.
            - The listing's category must exist in `product_categories`.
            - All required attributes for the category must be present in attribute_values.
            - All attribute values must be from the allowed set for that attribute (as defined in attribute_values and schema).
            - Listing must not already be published.
        """
        listing = self.seller_listings.get(listing_id)
        if not listing:
            return { "success": False, "error": f"Listing '{listing_id}' does not exist." }

        if listing["status"] == "published":
            return { "success": False, "error": f"Listing '{listing_id}' is already published." }

        category_id = listing["category_id"]
        if category_id not in self.product_categories:
            return { "success": False, "error": f"Category '{category_id}' for listing does not exist." }

        # Gather all attribute schemas for this category
        schemas = [
            schema for schema in self.attribute_schemas.values()
            if schema["category_id"] == category_id
        ]
        attr_values = listing["attribute_values"]

        # 1. Check required attributes
        for schema in schemas:
            attr_id = schema["attribute_id"]
            if schema["required"]:
                if attr_id not in attr_values or not attr_values[attr_id]:
                    return {
                        "success": False,
                        "error": f"Required attribute '{schema['name']}' is missing for listing '{listing_id}'."
                    }

        # 2. Check all provided attributes for allowed values
        for attr_id, value in attr_values.items():
            # Check attribute is in schema
            attr_schema = next((s for s in schemas if s["attribute_id"] == attr_id), None)
            if not attr_schema:
                return {
                    "success": False,
                    "error": f"Attribute '{attr_id}' is not valid for category '{category_id}'."
                }
            allowed_values = set(attr_schema.get("allowed_values", []))
            # Also consult AttributeValue for human-friendly checking
            attr_allowed_value_objs = self.attribute_values.get(attr_id, [])
            allowed_value_set = set([v["value"] for v in attr_allowed_value_objs])
            if allowed_values:
                allowed_value_set &= allowed_values  # Intersect if both used
            if value not in allowed_value_set:
                return {
                    "success": False,
                    "error": f"Value '{value}' is not allowed for attribute '{attr_schema['name']}' in listing '{listing_id}'."
                }

        # If all checks pass, mark as published
        listing["status"] = "published"
        self.seller_listings[listing_id] = listing
        return {
            "success": True,
            "message": f"Listing '{listing_id}' has been published."
        }

    def delete_listing(self, listing_id: str) -> dict:
        """
        Remove a seller's listing from the system.

        Args:
            listing_id (str): The unique identifier of the listing to delete.

        Returns:
            dict:
              - On success:
                  {"success": True, "message": "Listing <listing_id> has been deleted."}
              - On failure:
                  {"success": False, "error": "Listing does not exist."}

        Constraints:
            - Listing must exist in the system to be deleted.
        """
        if listing_id not in self.seller_listings:
            return {"success": False, "error": "Listing does not exist."}

        del self.seller_listings[listing_id]
        return {"success": True, "message": f"Listing {listing_id} has been deleted."}

    def change_listing_status(self, listing_id: str, new_status: str) -> dict:
        """
        Set the status of a seller listing.

        Args:
            listing_id (str): The ID of the listing to update.
            new_status (str): The new status to set (e.g., 'draft', 'published', 'removed').

        Returns:
            dict:
                - On success:
                    { "success": True, "message": "Listing status updated to <new_status>" }
                - On error:
                    { "success": False, "error": <reason> }

        Constraints:
            - Listing must exist.
            - If setting status to 'published', listing must be valid:
                - Category must exist.
                - All required attributes must be present.
                - All provided attribute values must be allowed for their attribute.
        """
        # Check if listing exists
        if listing_id not in self.seller_listings:
            return { "success": False, "error": "Listing does not exist" }
    
        listing = self.seller_listings[listing_id]
        category_id = listing['category_id']

        if new_status == "published":
            # Validate category existence
            if category_id not in self.product_categories:
                return { "success": False, "error": "Listing category does not exist" }
            # Gather all attribute schemas for this category
            schemas = [
                schema for schema in self.attribute_schemas.values()
                if schema['category_id'] == category_id
            ]
            # Validate required attributes are present
            for schema in schemas:
                attr_id = schema['attribute_id']
                if schema['required'] and attr_id not in listing['attribute_values']:
                    return { "success": False, "error": f"Missing required attribute: {schema['name']}" }
            # Validate provided attribute values
            for attr_id, value in listing['attribute_values'].items():
                # Check schema exists for this attribute
                schema = self.attribute_schemas.get(attr_id)
                if schema is None or schema['category_id'] != category_id:
                    return { "success": False, "error": f"Invalid attribute: {attr_id}" }
                # Check value allowed
                allowed_values = [v['value'] for v in self.attribute_values.get(attr_id, [])]
                if value not in allowed_values:
                    return { "success": False, "error": f"Value '{value}' not allowed for attribute: {schema['name']}" }
            # All validations passed, update status
            listing['status'] = new_status
            return { "success": True, "message": f"Listing status updated to '{new_status}'" }
        else:
            # No special validation, just update status
            listing['status'] = new_status
            return { "success": True, "message": f"Listing status updated to '{new_status}'" }


class MarketplaceProductListingManagementSystem(BaseEnv):
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

    def list_product_categories(self, **kwargs):
        return self._call_inner_tool('list_product_categories', kwargs)

    def get_category_by_id(self, **kwargs):
        return self._call_inner_tool('get_category_by_id', kwargs)

    def list_category_attribute_schemas(self, **kwargs):
        return self._call_inner_tool('list_category_attribute_schemas', kwargs)

    def get_attribute_schema_by_id(self, **kwargs):
        return self._call_inner_tool('get_attribute_schema_by_id', kwargs)

    def list_attribute_values(self, **kwargs):
        return self._call_inner_tool('list_attribute_values', kwargs)

    def list_seller_listings(self, **kwargs):
        return self._call_inner_tool('list_seller_listings', kwargs)

    def get_listing_by_id(self, **kwargs):
        return self._call_inner_tool('get_listing_by_id', kwargs)

    def create_listing(self, **kwargs):
        return self._call_inner_tool('create_listing', kwargs)

    def update_listing_attributes(self, **kwargs):
        return self._call_inner_tool('update_listing_attributes', kwargs)

    def validate_listing(self, **kwargs):
        return self._call_inner_tool('validate_listing', kwargs)

    def publish_listing(self, **kwargs):
        return self._call_inner_tool('publish_listing', kwargs)

    def delete_listing(self, **kwargs):
        return self._call_inner_tool('delete_listing', kwargs)

    def change_listing_status(self, **kwargs):
        return self._call_inner_tool('change_listing_status', kwargs)

