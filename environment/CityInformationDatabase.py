# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, Optional, TypedDict

_UNSET = object()



class CityInfo(TypedDict):
    city_id: str
    name: str
    country_id: str
    region_id: Optional[str]
    population: float
    area: float
    other_statistic: float

class CountryInfo(TypedDict):
    country_id: str
    country_name: str

class RegionInfo(TypedDict):
    region_id: str
    region_name: str
    country_id: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Cities: {city_id: CityInfo}
        # Attributes: city_id, name, country_id, region_id, population, area, other_statistic
        self.cities: Dict[str, CityInfo] = {}

        # Countries: {country_id: CountryInfo}
        # Attributes: country_id, country_name
        self.countries: Dict[str, CountryInfo] = {}

        # Regions: {region_id: RegionInfo}
        # Attributes: region_id, region_name, country_id
        self.regions: Dict[str, RegionInfo] = {}

        # Constraints:
        # - Each city must be associated with an existing country and (optionally) a region.
        # - City names are unique within the same country and region combination.
        # - City statistics (e.g., population, area) must be non-negative values.

    def list_all_cities(self) -> dict:
        """
        Retrieve a list of all cities in the database, including their primary attributes.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[CityInfo]
            }
            - On success, provides a list of city records (may be empty if no cities in database).
        """
        city_list = list(self.cities.values())
        return { "success": True, "data": city_list }

    def get_city_by_id(self, city_id: str) -> dict:
        """
        Fetch detailed information for a city given its unique city_id.

        Args:
            city_id (str): The unique identifier of the city to retrieve.

        Returns:
            dict: 
              - On success: {"success": True, "data": CityInfo}
              - On failure: {"success": False, "error": "City not found"}

        Constraints:
            - The city_id must exist in the system.
        """
        city = self.cities.get(city_id)
        if city is None:
            return {"success": False, "error": "City not found"}
        return {"success": True, "data": city}

    def search_cities_by_name(
        self,
        name: str,
        partial_match: bool = False,
        case_insensitive: bool = False
    ) -> dict:
        """
        Search for cities whose name matches the provided string.
    
        Args:
            name (str): Name or partial name to match.
            partial_match (bool, optional): If True, perform substring match (default: False = exact match).
            case_insensitive (bool, optional): If True, ignore case in matching (default: False).
    
        Returns:
            dict: {
                "success": True,
                "data": List[CityInfo],  # List of matching cities (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Error reason
            }
        
        Constraints:
            - 'name' must be a non-empty string.
            - No other constraints beyond CityInfo string matching.
        """

        if not isinstance(name, str) or name == "":
            return { "success": False, "error": "Search name must be a non-empty string." }
    
        results = []
        for city in self.cities.values():
            city_name = city["name"]
            search_name = name

            if case_insensitive:
                city_name = city_name.lower()
                search_name = name.lower()

            if partial_match:
                match = search_name in city_name
            else:
                match = search_name == city_name

            if match:
                results.append(city)

        return { "success": True, "data": results }

    def list_all_countries(self) -> dict:
        """
        Retrieve all countries currently stored in the database.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[CountryInfo],  # List of all country records,
            }

        Constraints:
            - None relevant.
        """
        result = list(self.countries.values())
        return { "success": True, "data": result }

    def get_country_by_id(self, country_id: str) -> dict:
        """
        Obtain details for a specific country given a country_id.

        Args:
            country_id (str): The unique identifier of the country.

        Returns:
            dict: {
                "success": True,
                "data": CountryInfo
            }
            or
            {
                "success": False,
                "error": str  # "Country not found"
            }

        Constraints:
            - The country_id must exist in the city information database.
        """
        country = self.countries.get(country_id)
        if country is None:
            return {"success": False, "error": "Country not found"}
        return {"success": True, "data": country}

    def list_all_regions(self) -> dict:
        """
        Retrieve a complete list of all regions in the database.

        Returns:
            dict: {
                "success": True,
                "data": List[RegionInfo]  # All regions; empty list if none exist.
            }

        Constraints:
            - None for this operation; it returns all existing regions.
        """
        regions_list = list(self.regions.values())
        return { "success": True, "data": regions_list }

    def get_region_by_id(self, region_id: str) -> dict:
        """
        Obtain details for a specific region given a region_id.

        Args:
            region_id (str): The unique identifier of the region.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": RegionInfo
                    }
                On failure (region does not exist):
                    {
                        "success": False,
                        "error": "Region not found"
                    }
        Constraints:
            - region_id must exist in the database.
        """
        region = self.regions.get(region_id)
        if region is None:
            return {"success": False, "error": "Region not found"}
        return {"success": True, "data": region}

    def list_cities_by_country(self, country_id: str) -> dict:
        """
        Retrieve all cities associated with the specified country_id.

        Args:
            country_id (str): The unique identifier for the country.

        Returns:
            dict: {
                "success": True,
                "data": List[CityInfo],  # List of matching cities (may be empty if no cities)
            }
            or
            {
                "success": False,
                "error": str  # E.g. "Country does not exist"
            }

        Constraints:
            - The given country_id must exist in the countries dictionary.
        """
        if country_id not in self.countries:
            return {"success": False, "error": "Country does not exist"}

        result = [
            city_info for city_info in self.cities.values()
            if city_info["country_id"] == country_id
        ]
        return {"success": True, "data": result}

    def list_cities_by_region(self, region_id: str) -> dict:
        """
        Retrieve all cities associated with a specified region_id.

        Args:
            region_id (str): The region's unique identifier.

        Returns:
            dict: {
                "success": True,
                "data": List[CityInfo],  # All cities with matching region_id
            }
            or
            {
                "success": False,
                "error": str  # Region does not exist
            }

        Constraints:
            - The region_id must exist within the database.
            - Returns an empty list if no matching cities found.
        """
        if region_id not in self.regions:
            return { "success": False, "error": "Region does not exist" }

        cities = [
            city for city in self.cities.values()
            if city["region_id"] == region_id
        ]

        return { "success": True, "data": cities }

    def get_city_statistics(self, city_id: str) -> dict:
        """
        Obtain the statistical fields (population, area, other_statistic) for a specific city.

        Args:
            city_id (str): Unique identifier of the city.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "population": float,
                    "area": float,
                    "other_statistic": float
                }
            }
            or
            {
                "success": False,
                "error": "City not found"
            }

        Constraints:
            - The city with the given ID must exist in the database.
        """
        city = self.cities.get(city_id)
        if not city:
            return {"success": False, "error": "City not found"}

        stats = {
            "population": city["population"],
            "area": city["area"],
            "other_statistic": city["other_statistic"]
        }
        return {"success": True, "data": stats}

    def add_city(
        self,
        city_id: str,
        name: str,
        country_id: str,
        region_id: Optional[str],
        population: float,
        area: float,
        other_statistic: float
    ) -> dict:
        """
        Add a new city to the database, validating country/region association and
        uniqueness of city name within country-region.

        Args:
            city_id (str): Unique city identifier.
            name (str): City name.
            country_id (str): Existing country ID.
            region_id (Optional[str]): Existing region ID (or None).
            population (float): Non-negative population.
            area (float): Non-negative area.
            other_statistic (float): Non-negative stat.

        Returns:
            dict: {
                "success": True,
                "message": "City added successfully."
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints checked:
            - Each city must be associated with an existing country and valid region (if provided).
            - region_id (if provided) must exist, and its country_id must match.
            - City names are unique within (country_id, region_id).
            - City statistics (population, area, other_statistic) must be non-negative.
            - city_id must be unique.
        """
        # Validate city_id uniqueness
        if city_id in self.cities:
            return { "success": False, "error": "City ID already exists." }

        # Validate country_id
        if country_id not in self.countries:
            return { "success": False, "error": "Country does not exist." }

        # Validate region_id if provided
        if region_id is not None:
            if region_id not in self.regions:
                return { "success": False, "error": "Region does not exist." }
            # Check that region belongs to the country
            if self.regions[region_id]["country_id"] != country_id:
                return { "success": False, "error": "Region does not belong to specified country." }

        # Validate non-negative statistics
        if population < 0:
            return { "success": False, "error": "Population must be non-negative." }
        if area < 0:
            return { "success": False, "error": "Area must be non-negative." }
        if other_statistic < 0:
            return { "success": False, "error": "Statistic must be non-negative." }

        # Validate name uniqueness within (country_id, region_id)
        for city in self.cities.values():
            if (city["name"] == name and
                city["country_id"] == country_id and
                city["region_id"] == region_id):
                return { "success": False, "error": "City name already exists in the specified country and region." }

        # Passed all checks, add the new city
        self.cities[city_id] = {
            "city_id": city_id,
            "name": name,
            "country_id": country_id,
            "region_id": region_id,
            "population": population,
            "area": area,
            "other_statistic": other_statistic
        }

        return { "success": True, "message": "City added successfully." }

    def update_city_info(
        self,
        city_id: str,
        name: str = None,
        country_id: str = None,
        region_id = _UNSET,
        population: float = None,
        area: float = None,
        other_statistic: float = None
    ) -> dict:
        """
        Update the attributes of an existing city while enforcing all database constraints.

        Args:
            city_id (str): The ID of the city to update.
            name (str, optional): New name for the city.
            country_id (str, optional): New country ID.
            region_id (str or None, optional): New region ID (can be None).
            population (float, optional): New population (must be non-negative).
            area (float, optional): New area (must be non-negative).
            other_statistic (float, optional): New statistic (must be non-negative).

        Returns:
            dict: {
                "success": True,
                "message": "City information updated."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - City must exist.
            - Updated country must exist.
            - Updated region must exist and belong to specified country if region_id is given.
            - Updated name must be unique within the (country_id, region_id) scope.
            - Statistics (population, area, other_statistic) must be non-negative if updated.
        """
        # Check if city exists
        if city_id not in self.cities:
            return { "success": False, "error": "City does not exist." }

        city = self.cities[city_id].copy()
        old_country_id = city["country_id"]
        old_region_id = city["region_id"]

        # Determine the effective country and region after update
        effective_country_id = country_id if country_id is not None else city["country_id"]
        effective_region_id = city["region_id"] if region_id is _UNSET else region_id

        # Check country exists if changed
        if country_id is not None and country_id not in self.countries:
            return { "success": False, "error": "Specified country does not exist." }

        # Check region validity after applying the requested change set.
        if effective_region_id is not None:
            if effective_region_id not in self.regions:
                return { "success": False, "error": "Specified region does not exist." }
            region_info = self.regions[effective_region_id]
            if region_info["country_id"] != effective_country_id:
                return {
                    "success": False,
                    "error": "Region does not belong to the specified country."
                }

        # Check statistic values
        for stat_name, val in [
            ("population", population),
            ("area", area),
            ("other_statistic", other_statistic)
        ]:
            if val is not None and val < 0:
                return { "success": False, "error": f"{stat_name} must be non-negative." }

        # Check uniqueness of city name within same (country, region)
        future_name = name if name is not None else city["name"]
        for cid, c in self.cities.items():
            if cid == city_id:
                continue
            if (
                c["name"] == future_name and
                c["country_id"] == effective_country_id and
                c["region_id"] == effective_region_id
            ):
                return {
                    "success": False,
                    "error": "City name must be unique within the same country and region."
                }

        # All checks passed, perform update only for specified fields
        if name is not None:
            city["name"] = name
        if country_id is not None:
            city["country_id"] = country_id
        if region_id is not _UNSET:
            city["region_id"] = region_id
        if population is not None:
            city["population"] = population
        if area is not None:
            city["area"] = area
        if other_statistic is not None:
            city["other_statistic"] = other_statistic

        self.cities[city_id] = city
        return { "success": True, "message": "City information updated." }

    def delete_city(self, city_id: str) -> dict:
        """
        Remove a city from the database by its city_id.

        Args:
            city_id (str): The unique identifier of the city to delete.

        Returns:
            dict:
                - On success: { "success": True, "message": "City deleted successfully." }
                - On failure: { "success": False, "error": "City not found." }

        Constraints:
            - The city_id must exist in the database to perform deletion.
        """
        if city_id not in self.cities:
            return { "success": False, "error": "City not found." }

        del self.cities[city_id]
        return { "success": True, "message": "City deleted successfully." }

    def add_country(self, country_id: str, country_name: str) -> dict:
        """
        Register a new country in the system.

        Args:
            country_id (str): Unique identifier for the country.
            country_name (str): Name of the country.

        Returns:
            dict: 
                - On success:
                    {"success": True, "message": "Country added successfully."}
                - On failure:
                    {"success": False, "error": <reason>}

        Constraints:
            - The country_id must be unique and must not already exist in the system.
            - country_id must not be empty.
        """
        if not country_id or not country_id.strip():
            return {"success": False, "error": "Country ID must not be empty."}
        if country_id in self.countries:
            return {"success": False, "error": f"Country ID '{country_id}' already exists."}

        self.countries[country_id] = {
            "country_id": country_id,
            "country_name": country_name
        }
        return {"success": True, "message": "Country added successfully."}

    def update_country_info(self, country_id: str, country_name: str = None) -> dict:
        """
        Update details of an existing country.

        Args:
            country_id (str): The unique ID of the country to update.
            country_name (str, optional): The new country name. If not provided, nothing is changed.

        Returns:
            dict, one of:
            { "success": True, "message": "Country information updated successfully." }
            { "success": False, "error": str }

        Constraints:
            - The country must exist to be updated.
            - Only defined fields (currently: country_name) may be updated.
        """
        if country_id not in self.countries:
            return { "success": False, "error": "Country ID does not exist." }
        if country_name is None:
            return { "success": True, "message": "No changes made." }
        self.countries[country_id]["country_name"] = country_name
        return { "success": True, "message": "Country information updated successfully." }

    def delete_country(self, country_id: str) -> dict:
        """
        Remove a country by country_id. This will also remove all regions and cities
        associated with this country, to maintain referential integrity.

        Args:
            country_id (str): The ID of the country to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Country, regions, and cities deleted."
            }
            or
            {
                "success": False,
                "error": "Country does not exist"
            }

        Constraints:
            - The country must exist.
            - All cities and regions linked to this country will also be deleted.
        """
        if country_id not in self.countries:
            return { "success": False, "error": "Country does not exist" }

        # Delete all cities associated with this country
        cities_to_delete = [city_id for city_id, city in self.cities.items() if city["country_id"] == country_id]
        for city_id in cities_to_delete:
            del self.cities[city_id]
    
        # Delete all regions associated with this country
        regions_to_delete = [region_id for region_id, region in self.regions.items() if region["country_id"] == country_id]
        for region_id in regions_to_delete:
            del self.regions[region_id]

        # Delete the country itself
        del self.countries[country_id]

        return { "success": True, "message": "Country, associated regions, and cities deleted." }

    def add_region(self, region_id: str, region_name: str, country_id: str) -> dict:
        """
        Register a new region within a specified country.

        Args:
            region_id (str): Unique region identifier.
            region_name (str): Name of the region (must not duplicate within the same country).
            country_id (str): Existing country ID to which the region belongs.

        Returns:
            dict: {
                "success": True,
                "message": "Region registered successfully."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - region_id must be unique (not already present in self.regions).
            - country_id must exist in self.countries.
            - region_name must be unique within the specified country.
            - All fields must be non-empty/non-None.
        """
        # Check all parameters provided
        if not region_id or not region_name or not country_id:
            return {"success": False, "error": "All fields (region_id, region_name, country_id) are required."}
        
        # Check region_id uniqueness
        if region_id in self.regions:
            return {"success": False, "error": "Region ID already exists."}

        # Check country existence
        if country_id not in self.countries:
            return {"success": False, "error": "Specified country does not exist."}
    
        # Check region_name uniqueness within the country
        for region in self.regions.values():
            if region["region_name"] == region_name and region["country_id"] == country_id:
                return {"success": False, "error": "A region with the same name already exists within the country."}

        # Register the new region
        new_region = {
            "region_id": region_id,
            "region_name": region_name,
            "country_id": country_id,
        }
        self.regions[region_id] = new_region

        return {"success": True, "message": "Region registered successfully."}

    def update_region_info(
        self, 
        region_id: str, 
        region_name: Optional[str] = None, 
        country_id: Optional[str] = None
    ) -> dict:
        """
        Update details for a region.

        Args:
            region_id (str): The ID of the region to update.
            region_name (Optional[str]): The new name for the region (if updating).
            country_id (Optional[str]): The new country ID for the region (if updating).

        Returns:
            dict: {
                "success": True,
                "message": "Region info updated successfully"
            } on success,
            or
            {
                "success": False,
                "error": "<reason>"
            } on failure.

        Constraints:
            - region_id must exist in the database.
            - If country_id is supplied, it must exist in the database.
            - At least one of region_name or country_id must be provided.
        """
        # Check: region must exist
        if region_id not in self.regions:
            return { "success": False, "error": "Region does not exist" }

        if region_name is None and country_id is None:
            return { "success": False, "error": "No update fields provided" }

        # If updating country_id, check the country exists
        if country_id is not None and country_id not in self.countries:
            return { "success": False, "error": "Specified country_id does not exist" }

        region_info = self.regions[region_id]
        # Update fields
        if region_name is not None:
            region_info["region_name"] = region_name
        if country_id is not None:
            region_info["country_id"] = country_id

        self.regions[region_id] = region_info  # Not strictly necessary; dict is mutable

        return { "success": True, "message": "Region info updated successfully" }

    def delete_region(self, region_id: str) -> dict:
        """
        Remove a region by its region_id. Any city associated with this region will have its `region_id` set to None.
    
        Args:
            region_id (str): The ID of the region to remove.
    
        Returns:
            dict: {
                "success": True,
                "message": "Region <region_id> deleted. <N> city records updated."
            }
            or
            {
                "success": False,
                "error": "Region does not exist"
            }
        Constraints:
            - The region must exist.
            - Any cities referencing this region will be updated to set 'region_id' = None.
        """
        if region_id not in self.regions:
            return {"success": False, "error": "Region does not exist"}

        affected = 0
        for city in self.cities.values():
            if city["region_id"] == region_id:
                city["region_id"] = None
                affected += 1
    
        del self.regions[region_id]

        return {
            "success": True,
            "message": f"Region {region_id} deleted. {affected} city records updated."
        }

    def update_city_statistic(
        self,
        city_id: str,
        population: Optional[float] = None,
        area: Optional[float] = None,
        other_statistic: Optional[float] = None
    ) -> dict:
        """
        Modify population, area, or other_statistic for a city, ensuring no negative values are set.

        Args:
            city_id (str): Unique identifier for the city.
            population (Optional[float]): New population value (if modifying).
            area (Optional[float]): New area value (if modifying).
            other_statistic (Optional[float]): New other_statistic value (if modifying).

        Returns:
            dict:
                - On success: { "success": True, "message": "City statistics updated." }
                - On error: { "success": False, "error": <reason> }

        Constraints:
            - All updated statistics must be non-negative values.
            - city_id must exist in cities.
        """
        if city_id not in self.cities:
            return { "success": False, "error": "City not found." }

        # Check negative values
        for k, v in [("population", population), ("area", area), ("other_statistic", other_statistic)]:
            if v is not None and v < 0:
                return { "success": False, "error": f"{k} cannot be negative." }

        # If nothing to update
        if population is None and area is None and other_statistic is None:
            return { "success": False, "error": "No values provided to update." }

        city = self.cities[city_id]
        if population is not None:
            city["population"] = population
        if area is not None:
            city["area"] = area
        if other_statistic is not None:
            city["other_statistic"] = other_statistic

        return { "success": True, "message": "City statistics updated." }


class CityInformationDatabase(BaseEnv):
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

    def list_all_cities(self, **kwargs):
        return self._call_inner_tool('list_all_cities', kwargs)

    def get_city_by_id(self, **kwargs):
        return self._call_inner_tool('get_city_by_id', kwargs)

    def search_cities_by_name(self, **kwargs):
        return self._call_inner_tool('search_cities_by_name', kwargs)

    def list_all_countries(self, **kwargs):
        return self._call_inner_tool('list_all_countries', kwargs)

    def get_country_by_id(self, **kwargs):
        return self._call_inner_tool('get_country_by_id', kwargs)

    def list_all_regions(self, **kwargs):
        return self._call_inner_tool('list_all_regions', kwargs)

    def get_region_by_id(self, **kwargs):
        return self._call_inner_tool('get_region_by_id', kwargs)

    def list_cities_by_country(self, **kwargs):
        return self._call_inner_tool('list_cities_by_country', kwargs)

    def list_cities_by_region(self, **kwargs):
        return self._call_inner_tool('list_cities_by_region', kwargs)

    def get_city_statistics(self, **kwargs):
        return self._call_inner_tool('get_city_statistics', kwargs)

    def add_city(self, **kwargs):
        return self._call_inner_tool('add_city', kwargs)

    def update_city_info(self, **kwargs):
        return self._call_inner_tool('update_city_info', kwargs)

    def delete_city(self, **kwargs):
        return self._call_inner_tool('delete_city', kwargs)

    def add_country(self, **kwargs):
        return self._call_inner_tool('add_country', kwargs)

    def update_country_info(self, **kwargs):
        return self._call_inner_tool('update_country_info', kwargs)

    def delete_country(self, **kwargs):
        return self._call_inner_tool('delete_country', kwargs)

    def add_region(self, **kwargs):
        return self._call_inner_tool('add_region', kwargs)

    def update_region_info(self, **kwargs):
        return self._call_inner_tool('update_region_info', kwargs)

    def delete_region(self, **kwargs):
        return self._call_inner_tool('delete_region', kwargs)

    def update_city_statistic(self, **kwargs):
        return self._call_inner_tool('update_city_statistic', kwargs)
