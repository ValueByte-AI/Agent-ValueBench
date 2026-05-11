# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Any



class PropertyInfo(TypedDict):
    property_id: str
    location_id: str
    property_manager_id: str
    address: str
    property_type: str
    amenities: List[str]  # List of amenity_ids
    rental_settings_id: str
    availability_status: str  # e.g., 'available', 'unavailable'

class AmenityInfo(TypedDict):
    amenity_id: str
    name: str
    description: str

class PropertyManagerInfo(TypedDict):
    manager_id: str
    name: str
    contact_info: str
    rating: float

class ReviewInfo(TypedDict):
    review_id: str
    property_id: str
    user_id: str
    rating: float
    comment: str
    date: str  # ISO 'YYYY-MM-DD'

class RentalSettingInfo(TypedDict):
    rental_settings_id: str
    price_per_night: float
    min_stay: int
    max_stay: int
    cancellation_policy: str

class RegionStatisticInfo(TypedDict):
    average_occupancy: float
    average_rating: float
    total_properties: int

class LocationRegionInfo(TypedDict):
    location_id: str
    name: str
    region_statistic: RegionStatisticInfo

class _GeneratedEnvImpl:
    def __init__(self):
        # Properties: {property_id: PropertyInfo}
        self.properties: Dict[str, PropertyInfo] = {}

        # Amenities: {amenity_id: AmenityInfo}
        self.amenities: Dict[str, AmenityInfo] = {}

        # Property amenities mapping: {property_id: [amenity_id, ...]}
        self.property_amenities: Dict[str, List[str]] = {}

        # Managers: {manager_id: PropertyManagerInfo}
        self.managers: Dict[str, PropertyManagerInfo] = {}

        # Reviews: {review_id: ReviewInfo}
        self.reviews: Dict[str, ReviewInfo] = {}

        # Rental settings: {rental_settings_id: RentalSettingInfo}
        self.rental_settings: Dict[str, RentalSettingInfo] = {}

        # Locations/Regions: {location_id: LocationRegionInfo}
        self.locations: Dict[str, LocationRegionInfo] = {}

        # Availability: {property_id: [date_str, ...]} -- dates in 'YYYY-MM-DD'
        self.availability: Dict[str, List[str]] = {}

        # Constraints:
        # - A property must have exactly one property manager.
        # - Each property listing must specify a location.
        # - Availability status and available_dates must be kept up to date.
        # - Reviews are linked to both the author and the property reviewed.
        # - Region statistics are updated dynamically as underlying property data changes.
        # - Only properties marked as available are shown in availability searches.

    def _normalize_property_amenity_links(self) -> None:
        for property_id, prop in self.properties.items():
            mapping_amenities = list(self.property_amenities.get(property_id, []))
            property_amenities = list(prop.get("amenities", []))
            merged = []
            for amenity_id in mapping_amenities + property_amenities:
                if amenity_id not in merged:
                    merged.append(amenity_id)
            self.property_amenities[property_id] = merged
            prop["amenities"] = list(merged)

    def get_location_by_name(self, name: str) -> dict:
        """
        Retrieve the location_id and details for a given region name.

        Args:
            name (str): The name of the region/location to look up (e.g., "Santa Monica").

        Returns:
            dict: {
                "success": True,
                "data": LocationRegionInfo  # The location data including location_id, name, region_statistic
            }
            OR
            {
                "success": False,
                "error": str  # "Region not found"
            }

        Constraints:
            - The name must match exactly (case-sensitive) to a region's name.
        """
        for location_info in self.locations.values():
            if location_info["name"] == name:
                return {"success": True, "data": location_info}
        return {"success": False, "error": "Region not found"}

    def list_available_properties_by_location(self, location_id: str) -> dict:
        """
        Retrieve all properties in a given location_id with status "available".

        Args:
            location_id (str): The identifier of the location/region.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[PropertyInfo]  # List of available properties in the location (may be empty)
                }
            or
                {
                    "success": False,
                    "error": str  # Location does not exist
                }

        Constraints:
            - location_id must exist.
            - Only properties where availability_status == "available" are returned.
        """
        if location_id not in self.locations:
            return {"success": False, "error": "Location does not exist"}

        result = [
            prop for prop in self.properties.values()
            if prop["location_id"] == location_id and prop["availability_status"] == "available"
        ]
        return {"success": True, "data": result}

    def get_property_details(self, property_id: str) -> dict:
        """
        Retrieve full details of a property (address, property_type, status, amenities, manager ID, rental_settings_id, location etc.) by property_id.

        Args:
            property_id (str): The unique identifier for the property.

        Returns:
            dict: {
               "success": True,
               "data": PropertyInfo  # All property details as stored
            }
            OR
            {
               "success": False,
               "error": str  # "Property not found" if invalid property_id
            }

        Constraints:
            - property_id must exist in self.properties.
        """
        prop = self.properties.get(property_id)
        if not prop:
            return { "success": False, "error": "Property not found" }
        return { "success": True, "data": prop }

    def get_property_amenities(self, property_id: str) -> dict:
        """
        Return a list of AmenityInfo for all amenities associated with a given property.

        Args:
            property_id (str): The unique identifier for the property.

        Returns:
            dict: {
                "success": True,
                "data": List[AmenityInfo]  # All amenities for the property (may be empty if none)
            }
            or
            {
                "success": False,
                "error": str  # Reason (e.g. property_id does not exist)
            }

        Constraints:
            - property_id must exist in the current properties.
            - Any amenity_id in the mapping but missing from self.amenities will be ignored.
        """
        if property_id not in self.properties:
            return { "success": False, "error": "Property does not exist" }

        amenity_ids = self.property_amenities.get(property_id)
        if amenity_ids is None:
            amenity_ids = self.properties[property_id].get("amenities", [])
        amenities_info = [
            self.amenities[amenity_id]
            for amenity_id in amenity_ids
            if amenity_id in self.amenities
        ]

        return { "success": True, "data": amenities_info }

    def get_amenity_info(self, amenity_id: str) -> dict:
        """
        Retrieve details for an amenity by its amenity_id.

        Args:
            amenity_id (str): The unique ID of the amenity.

        Returns:
            dict: 
              - On success: {"success": True, "data": AmenityInfo}
              - On failure: {"success": False, "error": str}
        Constraints:
            - The amenity must exist in the platform.
        """
        amenity = self.amenities.get(amenity_id)
        if not amenity:
            return {"success": False, "error": "Amenity not found"}

        return {"success": True, "data": amenity}

    def get_property_reviews(self, property_id: str) -> dict:
        """
        Fetch all reviews for a property ordered by date (descending, latest first).

        Args:
            property_id (str): The ID of the property whose reviews to fetch.

        Returns:
            dict: {
                "success": True,
                "data": List[ReviewInfo],  # ordered by date descending; empty if no reviews
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The property must exist.
            - All reviews are filtered and sorted by their 'date' field in descending order.
        """
        if property_id not in self.properties:
            return { "success": False, "error": "Property not found" }

        reviews = [
            review for review in self.reviews.values()
            if review["property_id"] == property_id
        ]
        # Sort reviews by date descending (latest first)
        reviews_sorted = sorted(reviews, key=lambda r: r["date"], reverse=True)
        return {"success": True, "data": reviews_sorted}

    def get_property_average_rating(self, property_id: str) -> dict:
        """
        Calculate and return the average rating for a property based on its reviews.

        Args:
            property_id (str): The ID of the property.

        Returns:
            dict: 
                - On success: { "success": True, "data": { "property_id": <str>, "average_rating": <float or None> } }
                - On failure: { "success": False, "error": <str> }

        Constraints:
            - The property_id must exist.
            - Returns None as average_rating if there are no reviews for the property.
        """
        if property_id not in self.properties:
            return { "success": False, "error": "Property not found" }

        ratings = [
            review["rating"]
            for review in self.reviews.values()
            if review["property_id"] == property_id
        ]

        if not ratings:
            avg = None
        else:
            avg = sum(ratings) / len(ratings)

        return {
            "success": True,
            "data": {
                "property_id": property_id,
                "average_rating": avg
            }
        }

    def get_property_manager_info(self, manager_id: str) -> dict:
        """
        Retrieve information about a property manager given a manager_id.

        Args:
            manager_id (str): The unique identifier for the property manager.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": PropertyManagerInfo
                }
                OR
                {
                    "success": False,
                    "error": "Manager not found"
                }

        Constraints:
            - manager_id must exist in self.managers.
        """
        if not manager_id or manager_id not in self.managers:
            return {"success": False, "error": "Manager not found"}
        return {"success": True, "data": self.managers[manager_id]}

    def get_property_rental_settings(self, property_id: str) -> dict:
        """
        Retrieve RentalSettingInfo for a property's rental_settings_id.

        Args:
            property_id (str): The unique identifier of the property.

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "data": RentalSettingInfo
                }
                On failure: {
                    "success": False,
                    "error": str
                }
        Constraints:
            - Property must exist in the platform.
            - Property must have a valid rental_settings_id.
            - The rental settings referenced must exist.
        """
        # Check if property exists
        prop = self.properties.get(property_id)
        if not prop:
            return {"success": False, "error": "Property not found"}

        rental_settings_id = prop.get("rental_settings_id")
        if not rental_settings_id:
            return {"success": False, "error": "Property missing rental_settings_id"}

        rental_settings = self.rental_settings.get(rental_settings_id)
        if not rental_settings:
            return {"success": False, "error": "Rental settings not found"}

        return {"success": True, "data": rental_settings}

    def get_region_statistics(self, location_id: str) -> dict:
        """
        Retrieve overview statistics for a given region/location.

        Args:
            location_id (str): The identifier of the location/region.

        Returns:
            dict: {
                "success": True,
                "data": RegionStatisticInfo  # {average_occupancy, average_rating, total_properties}
            }
            or
            {
                "success": False,
                "error": str  # If region/location not found or data missing
            }

        Constraints:
            - location_id must exist in the system.
            - Statistics may include: average_occupancy, average_rating, total_properties.
        """
        location = self.locations.get(location_id)
        if not location:
            return {"success": False, "error": "Location not found"}
        region_stat = location.get("region_statistic")
        if not region_stat:
            return {"success": False, "error": "Region statistics not found for this location"}
        return {"success": True, "data": region_stat}

    def list_amenities(self) -> dict:
        """
        Return a complete list of all available amenities on the platform.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[AmenityInfo]  # A list (possibly empty) of all AmenityInfo records.
            }
        """
        amenities_list = list(self.amenities.values())
        return { "success": True, "data": amenities_list }

    def get_property_availability_dates(self, property_id: str) -> dict:
        """
        List all available dates for a specified property by property_id.

        Args:
            property_id (str): The unique identifier of the property.

        Returns:
            dict:
                success: True and 'data': list of date strings in 'YYYY-MM-DD' format (may be empty)
                OR
                success: False and 'error': error message (if property does not exist)

        Constraints:
            - property_id must reference an existing property.
        """
        if property_id not in self.properties:
            return { "success": False, "error": "Property does not exist" }

        available_dates = self.availability.get(property_id, [])

        return { "success": True, "data": available_dates }

    def search_properties(
        self,
        location_id: str = None,
        location_name: str = None,
        min_price: float = None,
        max_price: float = None,
        required_amenities: list = None,  # amenity_ids or amenity_names (string)
        amenity_by_name: bool = False,
        available_dates: list = None,  # List[str]: required 'YYYY-MM-DD'
        property_type: str = None
    ) -> dict:
        """
        Search for available properties matching flexible filters.

        Args:
            location_id (str, optional): Location id to filter.
            location_name (str, optional): Location name to filter (if location_id is not provided).
            min_price (float, optional): Minimum nightly price.
            max_price (float, optional): Maximum nightly price.
            required_amenities (list, optional): List of amenity ids or names (see amenity_by_name).
            amenity_by_name (bool, optional): If True, interpret required_amenities as names, not ids.
            available_dates (list of str, optional): Dates that must all be available for the property (YYYY-MM-DD).
            property_type (str, optional): Filter by property type.

        Returns:
            dict: {
                "success": True,
                "data": [PropertyInfo, ...]  # List of matching PropertyInfo
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }
        Constraints:
            - Only available properties are returned.
            - If location_name given, must match an existing location.
            - Properties must match all provided filters to be included.
        """
        # Step 1: Location resolution
        if location_id is None and location_name is not None:
            # Try to find location_id by name (case-insensitive)
            for loc in self.locations.values():
                if loc["name"].lower() == location_name.lower():
                    location_id = loc["location_id"]
                    break
            if location_id is None:
                return { "success": False, "error": "location_name not found" }

        # Step 2: Amenity resolution
        amenity_ids = set()
        if required_amenities:
            if amenity_by_name:
                # Map names to amenity_ids
                amenity_name_to_id = {a["name"].lower(): a_id for a_id, a in self.amenities.items()}
                try:
                    for aname in required_amenities:
                        if aname.lower() not in amenity_name_to_id:
                            return { "success": False, "error": f"Amenity name '{aname}' not found" }
                        amenity_ids.add(amenity_name_to_id[aname.lower()])
                except Exception:
                    return { "success": False, "error": "Amenity name mapping error" }
            else:
                for aid in required_amenities:
                    if aid not in self.amenities:
                        return { "success": False, "error": f"Amenity id '{aid}' not found" }
                    amenity_ids.add(aid)

        # Build result
        results = []
        for prop in self.properties.values():
            if prop['availability_status'] != 'available':
                continue

            # Location filter
            if location_id is not None and prop["location_id"] != location_id:
                continue

            # Property type
            if property_type is not None and prop["property_type"] != property_type:
                continue

            # Amenities filter (intersection)
            if amenity_ids:
                prop_amenity_ids = set(self.property_amenities.get(prop["property_id"], []))
                if not amenity_ids.issubset(prop_amenity_ids):
                    continue

            # Price filter
            rental_setting = self.rental_settings.get(prop["rental_settings_id"])
            if rental_setting:
                price = rental_setting.get("price_per_night")
                if min_price is not None and price < min_price:
                    continue
                if max_price is not None and price > max_price:
                    continue

            # Date availability filter
            if available_dates:
                prop_dates = set(self.availability.get(prop["property_id"], []))
                if not set(available_dates).issubset(prop_dates):
                    continue

            results.append(prop)

        return { "success": True, "data": results }

    def set_property_availability_status(
        self,
        property_id: str,
        availability_status: str,
        available_dates: 'Optional[List[str]]' = None
    ) -> dict:
        """
        Update a property's availability_status and associated available_dates.

        Args:
            property_id (str): The ID of the property to update.
            availability_status (str): The new availability status ('available' or 'unavailable').
            available_dates (Optional[List[str]]): List of ISO date strings marking when the property is available.
                Required if availability_status is 'available'. Ignored and cleared if 'unavailable'.

        Returns:
            dict: 
                On success:
                    { "success": True, "message": "Property availability_status updated to <status>." }
                On failure:
                    { "success": False, "error": <reason> }
    
        Constraints:
            - property_id must exist.
            - If setting to 'available', at least one date must be provided.
            - If setting to 'unavailable', all available dates are cleared.
            - available_dates must be a list of ISO date strings.
        """
        if property_id not in self.properties:
            return {"success": False, "error": "Property does not exist"}

        status = availability_status.lower().strip()
        if status not in ('available', 'unavailable'):
            return {"success": False, "error": "Invalid availability_status. Must be 'available' or 'unavailable'."}

        if status == 'available':
            if not available_dates or not isinstance(available_dates, list) or not all(isinstance(d, str) for d in available_dates):
                return {"success": False, "error": "For 'available' status, non-empty list of date strings is required."}
            # Update status and available dates
            self.properties[property_id]['availability_status'] = 'available'
            self.availability[property_id] = available_dates
            return {"success": True, "message": f"Property availability_status updated to 'available'."}
        else:  # status == 'unavailable'
            self.properties[property_id]['availability_status'] = 'unavailable'
            self.availability[property_id] = []
            return {"success": True, "message": "Property availability_status updated to 'unavailable' and dates cleared."}

    def add_property(
        self,
        property_id: str,
        location_id: str,
        property_manager_id: str,
        address: str,
        property_type: str,
        amenities: list,
        rental_settings_id: str,
        availability_status: str
    ) -> dict:
        """
        Add a new property with all required details.

        Args:
            property_id (str): Unique identifier for the property.
            location_id (str): Must exist in self.locations.
            property_manager_id (str): Must exist in self.managers.
            address (str): Address of the property.
            property_type (str): Type of property (e.g., apartment, house).
            amenities (List[str]): List of amenity_ids (all must exist in self.amenities).
            rental_settings_id (str): Must exist in self.rental_settings.
            availability_status (str): Must be 'available' or 'unavailable'.

        Returns:
            dict: {
                "success": True,
                "message": "Property <property_id> added successfully."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Each property must have exactly one property manager (existence check).
            - Each property must specify a valid location.
            - All amenity_ids must be recognized.
            - The property_id must be unique.
            - The rental_settings_id must be valid.
            - Valid availability_status must be 'available' or 'unavailable'.
        """
        # Check property_id uniqueness
        if property_id in self.properties:
            return {"success": False, "error": "Property ID already exists."}
        # Check property_manager_id valid
        if property_manager_id not in self.managers:
            return {"success": False, "error": "Invalid property manager ID."}
        # Check location_id valid
        if location_id not in self.locations:
            return {"success": False, "error": "Invalid location ID."}
        # Check rental_settings_id valid
        if rental_settings_id not in self.rental_settings:
            return {"success": False, "error": "Invalid rental settings ID."}
        # Check amenities valid
        for amenity_id in amenities:
            if amenity_id not in self.amenities:
                return {"success": False, "error": f"Invalid amenity ID: {amenity_id}"}
        # Check availability_status
        if availability_status not in ("available", "unavailable"):
            return {"success": False, "error": "Invalid availability_status. Must be 'available' or 'unavailable'."}
        # Add property
        self.properties[property_id] = {
            "property_id": property_id,
            "location_id": location_id,
            "property_manager_id": property_manager_id,
            "address": address,
            "property_type": property_type,
            "amenities": amenities,
            "rental_settings_id": rental_settings_id,
            "availability_status": availability_status
        }
        # Set amenities mapping
        self.property_amenities[property_id] = amenities.copy()
        # Add to availability structure as empty list (dates to be set by other operations)
        self.availability[property_id] = []
        return {
            "success": True,
            "message": f"Property {property_id} added successfully."
        }

    def update_property_info(
        self,
        property_id: str,
        address: str = None,
        property_type: str = None,
        location_id: str = None,
        rental_settings_id: str = None
    ) -> dict:
        """
        Modify details (address, type, location, rental settings) of an existing property.

        Args:
            property_id (str): The ID of the property to update.
            address (str, optional): New address.
            property_type (str, optional): New property type.
            location_id (str, optional): New location ID (must exist).
            rental_settings_id (str, optional): New rental settings ID (must exist).

        Returns:
            dict: {
                "success": True,
                "message": "Property updated successfully."
            }
            or
            {
                "success": False,
                "error": ...  # Error description
            }

        Constraints:
            - property_id must exist.
            - location_id (if specified) must exist.
            - rental_settings_id (if specified) must exist.
            - Cannot update property_id.
            - property_manager_id may not be updated here.
        """
        # Check if property exists
        if property_id not in self.properties:
            return {"success": False, "error": "Property does not exist."}
    
        prop = self.properties[property_id]
        updated = False

        # Address
        if address is not None:
            prop["address"] = address
            updated = True
        # Property type
        if property_type is not None:
            prop["property_type"] = property_type
            updated = True
        # Location id
        if location_id is not None:
            if location_id not in self.locations:
                return {"success": False, "error": "Specified location_id does not exist."}
            prop["location_id"] = location_id
            updated = True
        # Rental settings id
        if rental_settings_id is not None:
            if rental_settings_id not in self.rental_settings:
                return {"success": False, "error": "Specified rental_settings_id does not exist."}
            prop["rental_settings_id"] = rental_settings_id
            updated = True
        # At least one field must be updated
        if not updated:
            return {"success": False, "error": "No valid update fields provided."}
    
        self.properties[property_id] = prop
        return {"success": True, "message": "Property updated successfully."}

    def assign_property_manager(self, property_id: str, manager_id: str) -> dict:
        """
        Assign or change the property manager for a property.

        Args:
            property_id (str): The unique identifier for the property.
            manager_id (str): The unique identifier for the property manager.

        Returns:
            dict:
                - On success: {"success": True, "message": "Property manager assigned to property."}
                - On failure: {"success": False, "error": str}
    
        Constraints:
            - The property must exist.
            - The manager must exist.
            - A property has exactly one property manager; previous manager (if any) is replaced.

        """
        # Check that property exists
        if property_id not in self.properties:
            return { "success": False, "error": "Property does not exist." }
    
        # Check that manager exists
        if manager_id not in self.managers:
            return { "success": False, "error": "Manager does not exist." }
    
        # Assign or change the manager
        self.properties[property_id]['property_manager_id'] = manager_id

        return { "success": True, "message": "Property manager assigned to property." }

    def add_property_amenity(self, property_id: str, amenity_id: str) -> dict:
        """
        Associate an existing amenity with a property.

        Args:
            property_id (str): The unique identifier for the property.
            amenity_id (str): The unique identifier for the amenity.

        Returns:
            dict: {
                "success": True,
                "message": "Amenity added to property"
            }
            or
            {
                "success": False,
                "error": str  # Description of the error
            }

        Constraints:
            - property_id must exist in self.properties.
            - amenity_id must exist in self.amenities.
            - Amenity is only associated once; duplicates will not be added.
            - Keeps both self.property_amenities and self.properties[property_id]['amenities'] consistent.
        """

        if property_id not in self.properties:
            return { "success": False, "error": "Property does not exist" }
        if amenity_id not in self.amenities:
            return { "success": False, "error": "Amenity does not exist" }

        # Initialize the mapping if absent
        if property_id not in self.property_amenities:
            self.property_amenities[property_id] = []
        if amenity_id not in self.property_amenities[property_id]:
            self.property_amenities[property_id].append(amenity_id)
        # Keep PropertyInfo amenities in sync
        if amenity_id not in self.properties[property_id]['amenities']:
            self.properties[property_id]['amenities'].append(amenity_id)

        return { "success": True, "message": "Amenity added to property" }

    def remove_property_amenity(self, property_id: str, amenity_id: str) -> dict:
        """
        Remove an amenity association from a property.

        Args:
            property_id (str): The property from which the amenity is to be removed.
            amenity_id (str): The amenity to remove from the property.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Amenity <amenity_id> removed from property <property_id>."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "<description of error>"
                    }

        Constraints:
            - The property and amenity must both exist.
            - The amenity must be associated with the property in order to remove it.
        """
        # Check if property exists
        if property_id not in self.properties:
            return { "success": False, "error": "Property does not exist." }
        # Check if amenity exists
        if amenity_id not in self.amenities:
            return { "success": False, "error": "Amenity does not exist." }
        # Check if property has an amenity list
        if property_id not in self.property_amenities:
            return { "success": False, "error": "No amenities associated with this property." }
        # Check if the amenity is associated
        if amenity_id not in self.property_amenities[property_id]:
            return { "success": False, "error": "Amenity is not associated with this property." }
        # Remove the amenity
        self.property_amenities[property_id].remove(amenity_id)
        # Also ensure property_info.amenities stays in sync if used
        if "amenities" in self.properties[property_id] and amenity_id in self.properties[property_id]["amenities"]:
            self.properties[property_id]["amenities"].remove(amenity_id)
        return {
            "success": True,
            "message": f"Amenity {amenity_id} removed from property {property_id}."
        }

    def add_review(
        self,
        review_id: str,
        property_id: str,
        user_id: str,
        rating: float,
        comment: str,
        date: str
    ) -> dict:
        """
        Add a new Review to the platform, linking it to a property and a user.

        Args:
            review_id (str): Unique identifier for the review.
            property_id (str): ID of the property to review (must exist).
            user_id (str): The authoring user’s identifier.
            rating (float): Star rating (must be within 1.0 and 5.0 inclusive).
            comment (str): Free-form textual comment.
            date (str): Date of review in 'YYYY-MM-DD' format.

        Returns:
            dict: {
                "success": True,
                "message": "Review added successfully."
            }
            OR
            dict: {
                "success": False,
                "error": <Reason for failure>
            }
        Constraints:
            - review_id must be unique.
            - property_id must exist.
            - rating must be between 1.0 and 5.0 inclusive.
            - date must be in 'YYYY-MM-DD' format.
        Side-effects:
            - May trigger update of region statistics after addition.
        """

        # Check for unique review_id
        if review_id in self.reviews:
            return {"success": False, "error": "Review ID already exists."}

        # Check property existence
        if property_id not in self.properties:
            return {"success": False, "error": "Property ID does not exist."}

        # Check rating range
        if not (1.0 <= rating <= 5.0):
            return {"success": False, "error": "Rating must be between 1.0 and 5.0."}

        # Check date format (basic check for 'YYYY-MM-DD')
        if not (isinstance(date, str) and len(date) == 10 and date[4] == '-' and date[7] == '-' and
                date[:4].isdigit() and date[5:7].isdigit() and date[8:].isdigit()):
            return {"success": False, "error": "Date must be in 'YYYY-MM-DD' format."}

        # Create new review
        review_info = {
            "review_id": review_id,
            "property_id": property_id,
            "user_id": user_id,
            "rating": rating,
            "comment": comment,
            "date": date,
        }
        self.reviews[review_id] = review_info

        # Update region statistics for the property's location
        property_info = self.properties[property_id]
        location_id = property_info["location_id"]
        if hasattr(self, "update_region_statistics"):
            self.update_region_statistics(location_id)

        return {"success": True, "message": "Review added successfully."}

    def update_region_statistics(self, location_id: str) -> dict:
        """
        Recalculate and update the aggregated statistics for a given location/region.
        Recomputes average occupancy, average rating, and total properties for the region.

        Args:
            location_id (str): The unique ID of the region/location to update.

        Returns:
            dict: {
                "success": True,
                "message": "Region statistics updated for location_id ..."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The location/region must exist.
            - Properties relevant to calculation are those assigned to the given location.
            - If no data exists for any field, corresponding value should be 0.
        """
        # Check location exists
        if location_id not in self.locations:
            return {"success": False, "error": "Location/region does not exist"}

        # Gather all properties in this location
        property_ids = [
            pid for pid, info in self.properties.items()
            if info["location_id"] == location_id
        ]
        total_properties = len(property_ids)

        # --- Average Rating ---
        ratings = []
        for property_id in property_ids:
            for review in self.reviews.values():
                if review["property_id"] == property_id:
                    ratings.append(review["rating"])
        average_rating = sum(ratings) / len(ratings) if ratings else 0.0

        # --- Average Occupancy ---
        # This environment does not track bookings or any other occupancy-specific source of truth.
        # Preserving the existing aggregate avoids corrupting official region statistics with a
        # fabricated 100% occupancy derived from availability-only state.
        current_stats = self.locations[location_id].get("region_statistic", {})
        if total_properties == 0:
            average_occupancy = 0.0
        else:
            average_occupancy = current_stats.get("average_occupancy", 0.0)

        # --- Update the region statistics ---
        self.locations[location_id]["region_statistic"] = {
            "average_occupancy": average_occupancy,
            "average_rating": average_rating,
            "total_properties": total_properties,
        }

        return {
            "success": True,
            "message": f"Region statistics updated for location_id {location_id}"
        }

    def modify_rental_settings(
        self,
        property_id: str,
        price_per_night: float = None,
        min_stay: int = None,
        max_stay: int = None,
        cancellation_policy: str = None
    ) -> dict:
        """
        Update the rental settings (price_per_night, min_stay, max_stay, cancellation_policy)
        for the specified property. Only fields provided (not None) are updated.

        Args:
            property_id (str): The ID of the property whose settings are to be modified.
            price_per_night (float, optional): New nightly price (must be >= 0).
            min_stay (int, optional): New minimum stay in nights (must be >= 1).
            max_stay (int, optional): New maximum stay in nights (must be >= min_stay, if min_stay provided, otherwise >= 1).
            cancellation_policy (str, optional): New cancellation policy.

        Returns:
            dict: {
                "success": True,
                "message": "Rental settings updated successfully."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }
    
        Constraints:
            - property_id must exist and be valid.
            - Only provided fields are updated.
            - price_per_night >= 0; min_stay >= 1; max_stay >= min_stay (if both provided).
            - rental_settings_id for property must exist.
        """
        property_info = self.properties.get(property_id)
        if property_info is None:
            return { "success": False, "error": "Property does not exist." }

        rental_settings_id = property_info.get("rental_settings_id")
        settings = self.rental_settings.get(rental_settings_id)
        if settings is None:
            return { "success": False, "error": "Rental settings not found for this property." }

        # Ensure that at least one field is being updated
        if all(arg is None for arg in [price_per_night, min_stay, max_stay, cancellation_policy]):
            return { "success": False, "error": "No rental setting fields provided to update." }

        # Validate and apply updates
        if price_per_night is not None:
            if not isinstance(price_per_night, (int, float)) or price_per_night < 0:
                return { "success": False, "error": "Invalid price_per_night. Must be non-negative number." }
            settings["price_per_night"] = float(price_per_night)
        if min_stay is not None:
            if not isinstance(min_stay, int) or min_stay < 1:
                return { "success": False, "error": "Invalid min_stay. Must be an integer >= 1." }
            settings["min_stay"] = min_stay
        if max_stay is not None:
            if not isinstance(max_stay, int) or max_stay < 1:
                return { "success": False, "error": "Invalid max_stay. Must be an integer >= 1." }
            # If min_stay provided also, enforce max_stay >= min_stay
            target_min_stay = min_stay if min_stay is not None else settings.get("min_stay")
            if max_stay < target_min_stay:
                return { "success": False, "error": "max_stay must be greater than or equal to min_stay." }
            settings["max_stay"] = max_stay
        if cancellation_policy is not None:
            if not isinstance(cancellation_policy, str) or not cancellation_policy.strip():
                return { "success": False, "error": "Invalid cancellation_policy." }
            settings["cancellation_policy"] = cancellation_policy.strip()

        self.rental_settings[rental_settings_id] = settings
        return { "success": True, "message": "Rental settings updated successfully." }

    def add_amenity(self, amenity_id: str, name: str, description: str) -> dict:
        """
        Add a new amenity to the platform amenity catalog.

        Args:
            amenity_id (str): Unique identifier for the amenity.
            name (str): Name/title of the amenity.
            description (str): Description of the amenity.
    
        Returns:
            dict: {
                "success": True,
                "message": "Amenity added successfully"
            }
            or
            {
                "success": False,
                "error": error message
            }
    
        Constraints:
            - amenity_id must be unique.
            - name must not be empty.
        """
        # Check for missing or empty fields
        if not amenity_id or not name:
            return {"success": False, "error": "Amenity ID and name must not be empty"}

        # Check for unique amenity_id
        if amenity_id in self.amenities:
            return {"success": False, "error": "Amenity with this ID already exists"}

        amenity: AmenityInfo = {
            "amenity_id": amenity_id,
            "name": name,
            "description": description
        }
        self.amenities[amenity_id] = amenity
        return {"success": True, "message": "Amenity added successfully"}

    def delete_property(self, property_id: str) -> dict:
        """
        Remove a property from the platform and update region statistics accordingly.

        Args:
            property_id (str): The ID of the property to be removed.

        Returns:
            dict:
                - On success: { "success": True, "message": "Property <property_id> deleted successfully" }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - Region statistics are updated dynamically as underlying property data changes.
            - Should remove associated property amenities, reviews, and availability entries.
            - If region/ location exists, should update its statistics.
        """
        # Check if property exists
        if property_id not in self.properties:
            return { "success": False, "error": "Property not found" }

        property_info = self.properties[property_id]
        location_id = property_info.get("location_id")

        # Remove from properties
        del self.properties[property_id]

        # Remove from property_amenities if present
        if property_id in self.property_amenities:
            del self.property_amenities[property_id]

        # Remove from availability
        if property_id in self.availability:
            del self.availability[property_id]

        # Remove all reviews associated with the property
        reviews_to_delete = [
            review_id for review_id, review in self.reviews.items()
            if review["property_id"] == property_id
        ]
        for review_id in reviews_to_delete:
            del self.reviews[review_id]

        # Update region statistics if location exists
        if location_id in self.locations:
            region_info = self.locations[location_id]
            stats = region_info["region_statistic"]

            # Update total_properties
            stats["total_properties"] = max(0, stats.get("total_properties", 1) - 1)

            # Recalculate average_rating (remaining reviews for location)
            property_ids_in_region = [
                pid for pid, pinfo in self.properties.items()
                if pinfo.get("location_id") == location_id
            ]

            # Gather all reviews for properties in this region
            region_reviews = [
                review for review in self.reviews.values()
                if review["property_id"] in property_ids_in_region
            ]
            # If no reviews left, average_rating should be 0
            if region_reviews:
                avg_rating = sum(r["rating"] for r in region_reviews) / len(region_reviews)
            else:
                avg_rating = 0.0
            stats["average_rating"] = avg_rating

            # Recalculate occupancy if needed (placeholder: could leave unchanged if not enough info)
            # Example: If occupancy can't be derived from states above, set to 0 if no properties
            if stats["total_properties"] == 0:
                stats["average_occupancy"] = 0.0

        return { "success": True, "message": f"Property {property_id} deleted successfully" }

    def update_available_dates(self, property_id: str, new_available_dates: list[str]) -> dict:
        """
        Update the available dates for a property to reflect reservation or unblocking.

        Args:
            property_id (str): The ID of the property whose availability is to be updated.
            new_available_dates (List[str]): The updated list of available dates in 'YYYY-MM-DD' format.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Available dates updated for property <property_id>."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Description of problem"
                    }

        Constraints:
            - property_id must exist.
            - Property's availability list and availability_status field must be kept consistent.
            - Date strings should be in 'YYYY-MM-DD' format.
        """
        # Check if property exists
        if property_id not in self.properties:
            return { "success": False, "error": "Property not found." }
    
        # Validate date format briefly (optional, can be omitted if strict validation isn't needed)
        for date_str in new_available_dates:
            if not isinstance(date_str, str) or len(date_str) != 10 or date_str[4] != '-' or date_str[7] != '-':
                return { "success": False, "error": f"Invalid date format: {date_str}. Dates should be 'YYYY-MM-DD'." }
    
        # Update availability
        self.availability[property_id] = list(sorted(set(new_available_dates)))
    
        # Update availability status in PropertyInfo
        if len(new_available_dates) > 0:
            self.properties[property_id]['availability_status'] = 'available'
        else:
            self.properties[property_id]['availability_status'] = 'unavailable'
    
        return {
            "success": True,
            "message": f"Available dates updated for property {property_id}."
        }


class RealEstateRentalPlatform(BaseEnv):
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
            if key == "update_region_statistics":
                setattr(env, "_update_region_statistics_state", copy.deepcopy(value))
                continue
            setattr(env, key, copy.deepcopy(value))
        if hasattr(env, "_normalize_property_amenity_links"):
            env._normalize_property_amenity_links()

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

    def get_location_by_name(self, **kwargs):
        return self._call_inner_tool('get_location_by_name', kwargs)

    def list_available_properties_by_location(self, **kwargs):
        return self._call_inner_tool('list_available_properties_by_location', kwargs)

    def get_property_details(self, **kwargs):
        return self._call_inner_tool('get_property_details', kwargs)

    def get_property_amenities(self, **kwargs):
        return self._call_inner_tool('get_property_amenities', kwargs)

    def get_amenity_info(self, **kwargs):
        return self._call_inner_tool('get_amenity_info', kwargs)

    def get_property_reviews(self, **kwargs):
        return self._call_inner_tool('get_property_reviews', kwargs)

    def get_property_average_rating(self, **kwargs):
        return self._call_inner_tool('get_property_average_rating', kwargs)

    def get_property_manager_info(self, **kwargs):
        return self._call_inner_tool('get_property_manager_info', kwargs)

    def get_property_rental_settings(self, **kwargs):
        return self._call_inner_tool('get_property_rental_settings', kwargs)

    def get_region_statistics(self, **kwargs):
        return self._call_inner_tool('get_region_statistics', kwargs)

    def list_amenities(self, **kwargs):
        return self._call_inner_tool('list_amenities', kwargs)

    def get_property_availability_dates(self, **kwargs):
        return self._call_inner_tool('get_property_availability_dates', kwargs)

    def search_properties(self, **kwargs):
        return self._call_inner_tool('search_properties', kwargs)

    def set_property_availability_status(self, **kwargs):
        return self._call_inner_tool('set_property_availability_status', kwargs)

    def add_property(self, **kwargs):
        return self._call_inner_tool('add_property', kwargs)

    def update_property_info(self, **kwargs):
        return self._call_inner_tool('update_property_info', kwargs)

    def assign_property_manager(self, **kwargs):
        return self._call_inner_tool('assign_property_manager', kwargs)

    def add_property_amenity(self, **kwargs):
        return self._call_inner_tool('add_property_amenity', kwargs)

    def remove_property_amenity(self, **kwargs):
        return self._call_inner_tool('remove_property_amenity', kwargs)

    def add_review(self, **kwargs):
        return self._call_inner_tool('add_review', kwargs)

    def update_region_statistics(self, **kwargs):
        return self._call_inner_tool('update_region_statistics', kwargs)

    def modify_rental_settings(self, **kwargs):
        return self._call_inner_tool('modify_rental_settings', kwargs)

    def add_amenity(self, **kwargs):
        return self._call_inner_tool('add_amenity', kwargs)

    def delete_property(self, **kwargs):
        return self._call_inner_tool('delete_property', kwargs)

    def update_available_dates(self, **kwargs):
        return self._call_inner_tool('update_available_dates', kwargs)
