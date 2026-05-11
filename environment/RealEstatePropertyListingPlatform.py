# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



class PropertyInfo(TypedDict):
    property_id: str
    status: str  # 'for sale' or 'for rent'
    location: str
    price: float
    num_bedrooms: int
    amenities: List[str]  # List of amenity_id
    seller_id: str

class AmenityInfo(TypedDict):
    amenity_id: str
    name: str

class SellerBrokerInfo(TypedDict):
    seller_id: str
    name: str
    contact_info: str
    agency: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for real estate property listing platform.
        """

        # Properties: {property_id: PropertyInfo}
        #   Maps each property ID to respective property details.
        self.properties: Dict[str, PropertyInfo] = {}

        # Amenities: {amenity_id: AmenityInfo}
        #   Maps amenity IDs to amenity metadata.
        self.amenities: Dict[str, AmenityInfo] = {}

        # Sellers/Brokers: {seller_id: SellerBrokerInfo}
        #   Maps seller IDs to seller/broker metadata.
        self.sellers: Dict[str, SellerBrokerInfo] = {}

        # Constraints:
        # - Each property is associated with one seller/broker.
        # - All amenities associated with a property must exist in the amenity catalog.
        # - Properties must have sufficient details for queries (num_bedrooms, sale/rent, location).
        # - No duplicate property listings for the same physical address under the same seller.

    def list_properties(self) -> dict:
        """
        Retrieve all property records in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[PropertyInfo]  # All properties, possibly empty.
            }
        Constraints:
            - No parameters.
            - No error if property list is empty; return empty list in data.
        """
        properties_list = list(self.properties.values())
        return {
            "success": True,
            "data": properties_list
        }

    def filter_properties(
        self,
        status: str = None,
        location: str = None,
        min_bedrooms: int = None,
        max_bedrooms: int = None,
        min_price: float = None,
        max_price: float = None
    ) -> dict:
        """
        Retrieve properties filtered by status, location, bedroom count, and price range.

        Args:
            status (str, optional): 'for sale' or 'for rent'
            location (str, optional): Location string to match exactly.
            min_bedrooms (int, optional): Minimum number of bedrooms.
            max_bedrooms (int, optional): Maximum number of bedrooms.
            min_price (float, optional): Minimum price (inclusive).
            max_price (float, optional): Maximum price (inclusive).

        Returns:
            dict: {
                "success": True,
                "data": List[PropertyInfo],  # filtered results
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - If specified, min values must not exceed max values (for bedrooms and price).
        """
        # Sanity check for range inputs
        if (min_bedrooms is not None) and (max_bedrooms is not None):
            if min_bedrooms > max_bedrooms:
                return {"success": False, "error": "min_bedrooms cannot be greater than max_bedrooms"}
        if (min_price is not None) and (max_price is not None):
            if min_price > max_price:
                return {"success": False, "error": "min_price cannot be greater than max_price"}

        filtered = []
        for prop in self.properties.values():
            if status is not None and prop["status"] != status:
                continue
            if location is not None and prop["location"] != location:
                continue
            if min_bedrooms is not None and prop["num_bedrooms"] < min_bedrooms:
                continue
            if max_bedrooms is not None and prop["num_bedrooms"] > max_bedrooms:
                continue
            if min_price is not None and prop["price"] < min_price:
                continue
            if max_price is not None and prop["price"] > max_price:
                continue
            filtered.append(prop)
        return {"success": True, "data": filtered}

    def get_property_by_id(self, property_id: str) -> dict:
        """
        Retrieve detailed information for a specific property by property_id.

        Args:
            property_id (str): Unique identifier of the property.

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "data": PropertyInfo
                }
                On failure: {
                    "success": False,
                    "error": "Property not found"
                }

        Constraints:
            - Property_id must exist in the listing platform.
        """
        property_info = self.properties.get(property_id)
        if not property_info:
            return {"success": False, "error": "Property not found"}
        return {"success": True, "data": property_info}

    def get_amenity_by_name(self, name: str) -> dict:
        """
        Look up the amenity_id and details for an amenity given its human-readable name.

        Args:
            name (str): The human-readable name of the amenity to look up.

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "data": AmenityInfo  # The matching amenity's info
                }
                On failure (not found): {
                    "success": False,
                    "error": "Amenity not found"
                }

        Notes:
            - Amenity name comparison is case-sensitive and exact.
            - If there are multiple amenities with the same name, returns the first one found.
        """
        for amenity in self.amenities.values():
            if amenity["name"] == name:
                return { "success": True, "data": amenity }
        return { "success": False, "error": "Amenity not found" }

    def list_amenities(self) -> dict:
        """
        Retrieve the full amenity catalog with amenity_id and name pairs.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[AmenityInfo],  # List of amenity records, each with amenity_id and name
            }

        Notes:
            - Returns an empty list if there are currently no amenities defined.
            - No error possible for this simple query.
        """
        amenities_list = list(self.amenities.values())
        return { "success": True, "data": amenities_list }

    def list_property_amenities(self, property_id: str) -> dict:
        """
        Retrieve all amenities (IDs and names) associated with a specific property.

        Args:
            property_id (str): The property ID to retrieve amenities for.

        Returns:
            dict: {
                "success": True,
                "data": List[{"amenity_id": str, "name": str}]
            }
            or
            {
                "success": False,
                "error": str  # Reason (e.g. property not found)
            }

        Constraints:
            - The property must exist.
            - Only amenities existing in the amenity catalog are returned. Invalid/missing amenities are skipped.
        """
        if property_id not in self.properties:
            return {"success": False, "error": "Property not found"}

        prop = self.properties[property_id]
        results = []
        for amenity_id in prop.get("amenities", []):
            amenity = self.amenities.get(amenity_id)
            if amenity is not None:
                results.append({"amenity_id": amenity["amenity_id"], "name": amenity["name"]})

        return {"success": True, "data": results}

    def get_seller_by_id(self, seller_id: str) -> dict:
        """
        Retrieve seller or broker information by seller_id.

        Args:
            seller_id (str): The unique ID of the seller or broker.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "seller_id": str,
                    "name": str,
                    "contact_info": str,
                    "agency": str
                }
            }
            or
            {
                "success": False,
                "error": str  # e.g., "Seller not found"
            }

        Constraints:
            - The seller/broker with the given seller_id must exist in the system.
        """
        seller_info = self.sellers.get(seller_id)
        if seller_info is None:
            return {"success": False, "error": "Seller not found"}

        return {"success": True, "data": dict(seller_info)}

    def get_seller_by_name(self, name: str) -> dict:
        """
        Retrieve metadata for sellers/brokers by their name.

        Args:
            name (str): The (possibly non-unique) name of the seller/broker.

        Returns:
            dict:
                - success: True and 'data' is a list of SellerBrokerInfo dicts (empty if not found).
                - success: False and 'error' string if no seller with that name exists.

        Notes:
            - Name matching is case sensitive.
            - If multiple sellers/brokers share the same name, all are returned.
        """
        matches = [
            seller_info
            for seller_info in self.sellers.values()
            if seller_info["name"] == name
        ]
        if not matches:
            return { "success": False, "error": f"No seller found with name '{name}'" }
        return { "success": True, "data": matches }

    def list_properties_by_seller(self, seller_id: str) -> dict:
        """
        List all properties associated with a given seller/broker.

        Args:
            seller_id (str): The unique ID of the seller/broker.

        Returns:
            dict:
                - {"success": True, "data": List[PropertyInfo]} if seller exists (list may be empty)
                - {"success": False, "error": str} if seller_id is invalid

        Constraints:
            - seller_id must exist in the sellers registry.
        """
        if seller_id not in self.sellers:
            return {"success": False, "error": "Seller ID does not exist"}
    
        properties = [
            property_info
            for property_info in self.properties.values()
            if property_info["seller_id"] == seller_id
        ]
        return {"success": True, "data": properties}

    def check_duplicate_property(self, location: str, seller_id: str) -> dict:
        """
        Verify whether a property with the same location/address already exists for a seller.

        Args:
            location (str): Physical address or location of the property.
            seller_id (str): The seller/broker's user ID.

        Returns:
            dict:
                - On success:
                    {
                      "success": True,
                      "is_duplicate": bool,
                      "duplicate_property_ids": List[str],  # List of matching property_ids, or empty if none
                    }
                - On failure:
                    {
                      "success": False,
                      "error": str  # Reason for the failure, e.g. "Seller not found"
                    }

        Constraints:
            - Only considers property listings for the exact same location under the given seller.
            - seller_id must exist in the sellers catalog.
        """
        if not location or not seller_id:
            return {"success": False, "error": "Missing required parameters: location and seller_id"}
        if seller_id not in self.sellers:
            return {"success": False, "error": "Seller not found"}

        duplicates = [
            prop["property_id"]
            for prop in self.properties.values()
            if prop["seller_id"] == seller_id and prop["location"] == location
        ]

        return {
            "success": True,
            "is_duplicate": len(duplicates) > 0,
            "duplicate_property_ids": duplicates
        }

    def add_property(
        self,
        property_id: str,
        status: str,
        location: str,
        price: float,
        num_bedrooms: int,
        amenities: List[str],
        seller_id: str
    ) -> dict:
        """
        Add a new property listing, ensuring all constraints are satisfied.

        Args:
            property_id (str): Unique identifier for the property.
            status (str): 'for sale' or 'for rent'.
            location (str): Address or description of property location.
            price (float): Listing price.
            num_bedrooms (int): Number of bedrooms.
            amenities (List[str]): List of amenity_ids.
            seller_id (str): ID of the associated seller/broker.

        Returns:
            dict: {
                "success": True,
                "message": "Property added successfully."
            }
            OR
            {
                "success": False,
                "error": "Reason for failure."
            }

        Constraints:
            - property_id must be unique.
            - seller_id must exist.
            - All amenities must exist in amenity catalog.
            - Must have num_bedrooms, status, and location.
            - No other property with the same location and seller_id.
        """
        # Check unique property_id
        if property_id in self.properties:
            return {"success": False, "error": "Property ID already exists."}
        # Check seller association
        if seller_id not in self.sellers:
            return {"success": False, "error": "Seller/Broker does not exist."}
        # Check amenities
        for amenity_id in amenities:
            if amenity_id not in self.amenities:
                return {"success": False, "error": f"Amenity ID '{amenity_id}' does not exist in catalog."}
        # Check minimal detail
        if (status not in ('for sale', 'for rent')
            or not location
            or not isinstance(num_bedrooms, int)
            or num_bedrooms < 0):
            return {"success": False, "error": "Insufficient or invalid details (status, location, num_bedrooms)."}

        # Check for duplicate property (same location and seller_id)
        for prop in self.properties.values():
            if prop['location'] == location and prop['seller_id'] == seller_id:
                return {"success": False, "error": "Duplicate property: same location listed by this seller."}

        # All checks pass. Add property.
        self.properties[property_id] = {
            "property_id": property_id,
            "status": status,
            "location": location,
            "price": price,
            "num_bedrooms": num_bedrooms,
            "amenities": list(amenities),  # make a copy
            "seller_id": seller_id
        }

        return {"success": True, "message": "Property added successfully."}

    def update_property_details(
        self,
        property_id: str,
        status: str = None,
        location: str = None,
        price: float = None,
        num_bedrooms: int = None
    ) -> dict:
        """
        Update the details of an existing property (status, location, price, num_bedrooms).
        Only fields provided (non-None) are updated.

        Args:
            property_id (str): The ID of the property to update.
            status (str, optional): New status ("for sale"/"for rent").
            location (str, optional): New address/location.
            price (float, optional): New price.
            num_bedrooms (int, optional): New bedroom count.

        Returns:
            dict: {
                "success": True,
                "message": "Property details updated."
            }
            OR
            {
                "success": False,
                "error": "Property not found." | 
                         "Duplicate property listing for address under this seller." |
                         "Cannot set required field to empty."
            }

        Constraints:
            - Property must exist.
            - No other property with the same location (excluding self) can exist under same seller.
            - Required fields (status, location, price, num_bedrooms) cannot be set to empty/None.
        """
        if property_id not in self.properties:
            return { "success": False, "error": "Property not found." }

        prop = self.properties[property_id]
        seller_id = prop["seller_id"]
        new_location = location if location is not None else prop["location"]

        # Check for duplicate property at this location & seller (excluding self)
        for pid, pinfo in self.properties.items():
            if pid != property_id and pinfo["seller_id"] == seller_id and pinfo["location"] == new_location:
                return {
                    "success": False,
                    "error": "Duplicate property listing for address under this seller."
                }

        # If updating any field, make sure not set to None/empty
        if status is not None:
            if not status.strip():
                return { "success": False, "error": "Cannot set required field to empty." }
            prop["status"] = status
        if location is not None:
            if not location.strip():
                return { "success": False, "error": "Cannot set required field to empty." }
            prop["location"] = location
        if price is not None:
            prop["price"] = price
        if num_bedrooms is not None:
            prop["num_bedrooms"] = num_bedrooms

        self.properties[property_id] = prop
        return { "success": True, "message": "Property details updated." }

    def add_amenity_to_property(self, property_id: str, amenity_id: str) -> dict:
        """
        Associate a catalog-listed amenity with a property.

        Args:
            property_id (str): The ID of the property to update.
            amenity_id (str): The amenity catalog ID to add to the property.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Amenity <amenity_id> added to property <property_id>." }
                - On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - Both property and amenity must exist.
            - Amenity must not already be associated with the property.
            - Only catalog-listed amenities can be associated.
        """
        # Check property exists
        if property_id not in self.properties:
            return { "success": False, "error": "Property does not exist." }
        # Check amenity exists in catalog
        if amenity_id not in self.amenities:
            return { "success": False, "error": "Amenity does not exist in the amenity catalog." }
        # Check if already associated
        if amenity_id in self.properties[property_id]['amenities']:
            return { "success": False, "error": "Amenity already associated with this property." }
    
        # Add the amenity
        self.properties[property_id]['amenities'].append(amenity_id)
        return { 
            "success": True, 
            "message": f"Amenity {amenity_id} added to property {property_id}." 
        }

    def remove_amenity_from_property(self, property_id: str, amenity_id: str) -> dict:
        """
        Disassociate (remove) an amenity from a property.

        Args:
            property_id (str): ID of the property to update.
            amenity_id (str): ID of the amenity to remove.

        Returns:
            dict: 
                - If successful:
                    { "success": True, "message": "Amenity <amenity_id> removed from property <property_id>." }
                - If failure:
                    { "success": False, "error": "<reason>" }

        Constraints:
            - Property and amenity must both exist.
            - Amenity must be currently associated with the property.
            - After removal, property.amenities must only contain amenity_ids existing in the amenity catalog.
        """
        # Check if property exists
        if property_id not in self.properties:
            return { "success": False, "error": f"Property '{property_id}' does not exist" }
    
        # Check if amenity exists in catalog
        if amenity_id not in self.amenities:
            return { "success": False, "error": f"Amenity '{amenity_id}' does not exist in the amenity catalog" }
    
        property_info = self.properties[property_id]
        if amenity_id not in property_info["amenities"]:
            return { "success": False, "error": f"Amenity '{amenity_id}' is not associated with property '{property_id}'" }
    
        # Remove the amenity from the property's amenities list
        property_info["amenities"].remove(amenity_id)
        return { "success": True, "message": f"Amenity '{amenity_id}' removed from property '{property_id}'." }

    def add_amenity(self, amenity_id: str, name: str) -> dict:
        """
        Add a new amenity type to the amenity catalog.

        Args:
            amenity_id (str): Unique identifier for the new amenity.
            name (str): Human-readable name for the amenity.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Amenity added successfully." }
                On failure:
                    { "success": False, "error": <description of the error> }
    
        Constraints:
            - amenity_id must be unique within the catalog.
            - Both amenity_id and name must be non-empty strings.
        """
        if not isinstance(amenity_id, str) or not amenity_id.strip():
            return { "success": False, "error": "Amenity ID must be a non-empty string." }
        if not isinstance(name, str) or not name.strip():
            return { "success": False, "error": "Amenity name must be a non-empty string." }
        if amenity_id in self.amenities:
            return { "success": False, "error": f"Amenity ID '{amenity_id}' already exists." }

        amenity_info: AmenityInfo = {
            "amenity_id": amenity_id,
            "name": name
        }
        self.amenities[amenity_id] = amenity_info
        return { "success": True, "message": "Amenity added successfully." }

    def update_amenity(self, amenity_id: str, name: str = None) -> dict:
        """
        Update the details (e.g. name) of an amenity in the amenity catalog.

        Args:
            amenity_id (str): The unique ID of the amenity to update.
            name (str, optional): New name of the amenity.

        Returns:
            dict: {
                "success": True,
                "message": "Updated amenity details for <amenity_id>"
            }
            or {
                "success": False,
                "error": "Amenity not found" | "No update fields provided"
            }

        Constraints:
            - Amenity must exist in the catalog to be updated.
            - At least one updatable field must be provided.
        """
        if amenity_id not in self.amenities:
            return { "success": False, "error": "Amenity not found" }

        if name is None:
            return { "success": False, "error": "No update fields provided" }

        self.amenities[amenity_id]["name"] = name
        return { "success": True, "message": f"Updated amenity details for {amenity_id}" }

    def add_seller(
        self,
        seller_id: str,
        name: str,
        contact_info: str,
        agency: str
    ) -> dict:
        """
        Add a new seller/broker entry to the platform.

        Args:
            seller_id (str): Unique identifier for the seller/broker.
            name (str): Seller/broker's name.
            contact_info (str): Contact information for the seller/broker.
            agency (str): Agency or company the seller/broker belongs to.

        Returns:
            dict: {
                "success": True,
                "message": "Seller added successfully."
            }
            or
            {
                "success": False,
                "error": "Seller ID already exists."
            }

        Constraints:
            - seller_id must be unique in the platform.
        """
        if seller_id in self.sellers:
            return { "success": False, "error": "Seller ID already exists." }

        new_seller = {
            "seller_id": seller_id,
            "name": name,
            "contact_info": contact_info,
            "agency": agency
        }
        self.sellers[seller_id] = new_seller
        return { "success": True, "message": "Seller added successfully." }

    def update_seller_details(
        self, seller_id: str, name: str = None, contact_info: str = None, agency: str = None
    ) -> dict:
        """
        Update details of an existing seller/broker.

        Args:
            seller_id (str): Unique ID of seller/broker to update.
            name (str, optional): New name of the seller/broker.
            contact_info (str, optional): New contact information.
            agency (str, optional): New agency name.

        Returns:
            dict: {
                "success": True,
                "message": "Seller details updated successfully"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
        - seller_id must exist in the platform.
        - At least one updatable field (name, contact_info, agency) must be provided.
        """
        if seller_id not in self.sellers:
            return { "success": False, "error": "Seller not found" }

        # Check if any field to update is provided
        if name is None and contact_info is None and agency is None:
            return { "success": False, "error": "No update fields provided" }

        seller = self.sellers[seller_id]
        updated = False
        if name is not None:
            seller["name"] = name
            updated = True
        if contact_info is not None:
            seller["contact_info"] = contact_info
            updated = True
        if agency is not None:
            seller["agency"] = agency
            updated = True

        if updated:
            self.sellers[seller_id] = seller
            return { "success": True, "message": "Seller details updated successfully" }
        else:
            return { "success": False, "error": "No valid update performed" }

    def delete_property_listing(self, property_id: str) -> dict:
        """
        Remove a property listing from the platform.

        Args:
            property_id (str): The unique identifier for the property to delete.

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "message": "Property <property_id> deleted successfully."
                }
                On failure: {
                    "success": False,
                    "error": "Property not found."
                }

        Constraints:
            - The provided property_id must exist in the platform.
        """
        if property_id not in self.properties:
            return { "success": False, "error": "Property not found." }

        del self.properties[property_id]
        return { "success": True, "message": f"Property {property_id} deleted successfully." }

    def delete_amenity(self, amenity_id: str) -> dict:
        """
        Remove an amenity from the amenities catalog if it is not currently used by any property.

        Args:
            amenity_id (str): The amenity ID to be removed.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Amenity <amenity_id> deleted."
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Explanation of the error
                    }

        Constraints:
            - Amenity must exist in self.amenities.
            - Amenity must not be referenced by any property in self.properties.
        """
        # Check if amenity exists
        if amenity_id not in self.amenities:
            return { "success": False, "error": f"Amenity '{amenity_id}' does not exist." }

        # Check if amenity is referenced by any property
        for prop in self.properties.values():
            if amenity_id in prop.get("amenities", []):
                return {
                    "success": False,
                    "error": f"Amenity '{amenity_id}' is still used by one or more properties and cannot be deleted."
                }

        # Remove the amenity
        del self.amenities[amenity_id]
        return {
            "success": True,
            "message": f"Amenity '{amenity_id}' deleted."
        }

    def delete_seller(self, seller_id: str) -> dict:
        """
        Remove a seller/broker by seller_id. 
        Also deletes all properties associated with this seller (cascading delete).

        Args:
            seller_id (str): The ID of the seller/broker to delete.

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "message": str  # Seller and N properties deleted
                }
                On failure: {
                    "success": False,
                    "error": str  # Reason (e.g., seller not found)
                }
        Constraints:
            - Seller must exist in platform.
            - All their properties are deleted along with seller.
        """
        if seller_id not in self.sellers:
            return {"success": False, "error": "Seller not found"}

        # Find properties associated with this seller
        properties_to_delete = [
            prop_id for prop_id, prop in self.properties.items()
            if prop["seller_id"] == seller_id
        ]

        # Delete properties
        for prop_id in properties_to_delete:
            del self.properties[prop_id]

        # Delete seller/broker
        del self.sellers[seller_id]

        return {
            "success": True,
            "message": f"Seller '{seller_id}' deleted. {len(properties_to_delete)} associated property(ies) also removed."
        }


class RealEstatePropertyListingPlatform(BaseEnv):
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

    def list_properties(self, **kwargs):
        return self._call_inner_tool('list_properties', kwargs)

    def filter_properties(self, **kwargs):
        return self._call_inner_tool('filter_properties', kwargs)

    def get_property_by_id(self, **kwargs):
        return self._call_inner_tool('get_property_by_id', kwargs)

    def get_amenity_by_name(self, **kwargs):
        return self._call_inner_tool('get_amenity_by_name', kwargs)

    def list_amenities(self, **kwargs):
        return self._call_inner_tool('list_amenities', kwargs)

    def list_property_amenities(self, **kwargs):
        return self._call_inner_tool('list_property_amenities', kwargs)

    def get_seller_by_id(self, **kwargs):
        return self._call_inner_tool('get_seller_by_id', kwargs)

    def get_seller_by_name(self, **kwargs):
        return self._call_inner_tool('get_seller_by_name', kwargs)

    def list_properties_by_seller(self, **kwargs):
        return self._call_inner_tool('list_properties_by_seller', kwargs)

    def check_duplicate_property(self, **kwargs):
        return self._call_inner_tool('check_duplicate_property', kwargs)

    def add_property(self, **kwargs):
        return self._call_inner_tool('add_property', kwargs)

    def update_property_details(self, **kwargs):
        return self._call_inner_tool('update_property_details', kwargs)

    def add_amenity_to_property(self, **kwargs):
        return self._call_inner_tool('add_amenity_to_property', kwargs)

    def remove_amenity_from_property(self, **kwargs):
        return self._call_inner_tool('remove_amenity_from_property', kwargs)

    def add_amenity(self, **kwargs):
        return self._call_inner_tool('add_amenity', kwargs)

    def update_amenity(self, **kwargs):
        return self._call_inner_tool('update_amenity', kwargs)

    def add_seller(self, **kwargs):
        return self._call_inner_tool('add_seller', kwargs)

    def update_seller_details(self, **kwargs):
        return self._call_inner_tool('update_seller_details', kwargs)

    def delete_property_listing(self, **kwargs):
        return self._call_inner_tool('delete_property_listing', kwargs)

    def delete_amenity(self, **kwargs):
        return self._call_inner_tool('delete_amenity', kwargs)

    def delete_seller(self, **kwargs):
        return self._call_inner_tool('delete_seller', kwargs)

