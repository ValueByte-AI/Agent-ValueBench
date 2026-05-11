# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



class LocationInfo(TypedDict):
    location_id: str
    city_name: str
    country: str
    region_coordinate: str  # Could be a string or custom type; keeping it as str for now

class AirQualityMeasurementInfo(TypedDict):
    measurement_id: str
    location_id: str
    timestamp: str  # Could be float or datetime; using str for generality
    AQI: float
    main_pollutant: str

class PollutantLevelInfo(TypedDict):
    measurement_id: str
    pollutant_type: str
    concentration: float

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for tracking air quality data by location and time.
        """

        # Locations: {location_id: LocationInfo}
        # Represents each city/region being tracked.
        self.locations: Dict[str, LocationInfo] = {}

        # Air Quality Measurements: {measurement_id: AirQualityMeasurementInfo}
        # Each measurement refers to a location and a point in time.
        self.measurements: Dict[str, AirQualityMeasurementInfo] = {}

        # Pollutant Levels: {measurement_id: List[PollutantLevelInfo]}
        # For each measurement, records pollutant concentrations.
        self.pollutant_levels: Dict[str, List[PollutantLevelInfo]] = {}

        # Constraints:
        # - Each AirQualityMeasurement is associated with a single Location at a specific timestamp.
        # - Each AirQualityMeasurement must have at least all standard pollutant concentrations (e.g., for NO2, PM2.5, O3, etc.).
        # - The main_pollutant attribute reflects the pollutant with the greatest impact on the AQI for that measurement.
        # - AQI values are computed based on pollutant concentrations using regulatory formulas.

    def get_location_by_city_country(self, city_name: str, country: str) -> dict:
        """
        Retrieve the Location entity (information) for the given city and country.

        Args:
            city_name (str): The city to search for.
            country (str): The country to search for.

        Returns:
            dict:
                - If found: { "success": True, "data": LocationInfo }
                - If not found: { "success": False, "error": "Location not found" }

        Notes:
            - The operation performs a case-sensitive match on both city and country.
            - Returns the first matching location found.
        """
        for location in self.locations.values():
            if location["city_name"] == city_name and location["country"] == country:
                return { "success": True, "data": location }
        return { "success": False, "error": "Location not found" }

    def list_locations(self) -> dict:
        """
        List all tracked locations with metadata (id, city, country, region).

        Returns:
            dict: {
                "success": True,
                "data": List[LocationInfo]  # List of all locations (may be empty)
            }

        Constraints:
            - None. Lists all entries in the locations dictionary.
        """
        locations_list = list(self.locations.values())
        return { "success": True, "data": locations_list }

    def get_latest_measurement_for_location(self, location_id: str) -> dict:
        """
        Retrieve the most recent Air Quality Measurement for a specific location.

        Args:
            location_id (str): The unique identifier of the location.

        Returns:
            dict: {
                "success": True,
                "data": AirQualityMeasurementInfo  # Most recent measurement,
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure: non-existent location or no measurements available.
            }

        Constraints:
            - The given location must exist.
            - If no measurement exists for the location, return a failure.
            - The returned measurement has the latest (max) timestamp for the location.
        """
        # Check if the location exists
        if location_id not in self.locations:
            return { "success": False, "error": "Location does not exist" }
    
        # Find the measurements for the location
        location_measurements = [
            m for m in self.measurements.values()
            if m["location_id"] == location_id
        ]
        if not location_measurements:
            return { "success": False, "error": "No measurements available for this location" }

        # Find the measurement with the latest timestamp
        # Assuming ISO format or lexicographically comparable timestamps
        latest_measurement = max(
            location_measurements, key=lambda m: m["timestamp"]
        )

        return { "success": True, "data": latest_measurement }

    def get_measurement_by_id(self, measurement_id: str) -> dict:
        """
        Retrieve details for a specific air quality measurement by its ID.

        Args:
            measurement_id (str): The unique identifier for the measurement.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": AirQualityMeasurementInfo
                    }
                On failure (ID not found):
                    {
                        "success": False,
                        "error": "Measurement ID not found"
                    }

        Constraints:
            - The provided measurement_id must exist in the system.
        """
        if measurement_id not in self.measurements:
            return {"success": False, "error": "Measurement ID not found"}

        measurement_info = self.measurements[measurement_id]
        return {"success": True, "data": measurement_info}

    def get_AQI_and_main_pollutant(self, measurement_id: str) -> dict:
        """
        For a given air quality measurement, return its AQI value and main pollutant type.

        Args:
            measurement_id (str): The unique identifier for the air quality measurement.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "AQI": float,
                    "main_pollutant": str
                }
            }
            or
            {
                "success": False,
                "error": str  # e.g., if measurement_id not found
            }

        Constraints:
            - The measurement_id must exist in the measurements collection.
            - The measurement must have AQI and main_pollutant attributes assigned.
        """
        measurement = self.measurements.get(measurement_id)
        if measurement is None:
            return { "success": False, "error": "Measurement not found" }

        # Sanity check for required fields
        if ("AQI" not in measurement) or ("main_pollutant" not in measurement):
            return { "success": False, "error": "Measurement record incomplete" }

        return {
            "success": True,
            "data": {
                "AQI": measurement["AQI"],
                "main_pollutant": measurement["main_pollutant"]
            }
        }

    def get_pollutant_levels_for_measurement(self, measurement_id: str) -> dict:
        """
        For a given measurement_id, list all pollutant types and their concentrations.

        Args:
            measurement_id (str): The ID of the air quality measurement.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[PollutantLevelInfo]  # May be empty if no pollutants recorded
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason for failure
                    }

        Constraints:
            - The measurement_id must exist in the system.
        """
        if measurement_id not in self.measurements:
            return {"success": False, "error": "Measurement does not exist"}

        pollutant_levels = self.pollutant_levels.get(measurement_id, [])
        return {"success": True, "data": pollutant_levels}

    def get_pollutant_concentration(self, measurement_id: str, pollutant_type: str) -> dict:
        """
        Retrieve the concentration value for the given pollutant type within a specific measurement.

        Args:
            measurement_id (str): Unique identifier for the air quality measurement.
            pollutant_type (str): Type of pollutant (e.g., "NO2", "PM2.5", "O3").

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": float   # concentration value for the pollutant
                    }
                - On error:
                    {
                        "success": False,
                        "error": str    # Message explaining the missing data or problem
                    }
        Constraints:
            - The measurement must exist, and the pollutant_type must be present for that measurement.
        """
        # Check if measurement_id exists and has pollutant levels
        if measurement_id not in self.measurements:
            return { "success": False, "error": "Measurement ID does not exist" }

        if measurement_id not in self.pollutant_levels:
            return { "success": False, "error": "No pollutant data for this measurement" }

        for pl in self.pollutant_levels[measurement_id]:
            if pl["pollutant_type"] == pollutant_type:
                return { "success": True, "data": pl["concentration"] }

        return { "success": False, "error": f"Pollutant type '{pollutant_type}' not found for this measurement" }

    def list_measurements_for_location(
        self,
        location_id: str,
        start_time: str = None,
        end_time: str = None
    ) -> dict:
        """
        Lists all air quality measurements for a given location_id, optionally within a time range.

        Args:
            location_id (str): The location to filter measurements for. Must exist.
            start_time (str, optional): Minimum timestamp (inclusive) (ISO format or comparable string). Default: None.
            end_time (str, optional): Maximum timestamp (inclusive) (ISO format or comparable string). Default: None.

        Returns:
            dict:
                - success: True and data: List[AirQualityMeasurementInfo] if found (can be empty)
                - success: False and error: str if location_id is invalid

        Constraints:
            - location_id must exist in the system.
            - If start_time and/or end_time are provided, only measurements within [start_time, end_time] (inclusive) are included.
        """
        if location_id not in self.locations:
            return { "success": False, "error": "Location not found" }

        result = []
        for m in self.measurements.values():
            if m["location_id"] != location_id:
                continue
            ts = m["timestamp"]
            if start_time is not None and ts < start_time:
                continue
            if end_time is not None and ts > end_time:
                continue
            result.append(m)

        # Optionally, sort by timestamp ascending for consistency
        result.sort(key=lambda x: x["timestamp"])
        return { "success": True, "data": result }

    def add_air_quality_measurement(
        self,
        measurement_id: str,
        location_id: str,
        timestamp: str,
        AQI: float,
        main_pollutant: str,
        pollutant_levels: list
    ) -> dict:
        """
        Add a new Air Quality Measurement record for a location.

        Args:
            measurement_id (str): Unique identifier for the measurement.
            location_id (str): The ID of the location (must exist in self.locations).
            timestamp (str): ISO or other standard string representing the timestamp.
            AQI (float): Computed Air Quality Index value.
            main_pollutant (str): The pollutant with greatest impact on AQI for this record.
            pollutant_levels (list of dict): Each dict must have 'pollutant_type' (str) and 'concentration' (float).
                                            Must include at least all standard pollutants: NO2, PM2.5, O3.

        Returns:
            dict: On success, { "success": True, "message": ... }
                  On failure, { "success": False, "error": ... }

        Constraints:
            - measurement_id must be unique.
            - location_id must refer to an existing location.
            - All standard pollutants must be present.
            - main_pollutant must be one of the pollutants in pollutant_levels.
        """
        standard_pollutants = {"NO2", "PM2.5", "O3"}
        # Uniqueness of measurement_id
        if measurement_id in self.measurements:
            return { "success": False, "error": "Measurement ID already exists" }
        # Location existence
        if location_id not in self.locations:
            return { "success": False, "error": "Location ID does not exist" }
        # Check pollutant_levels structure and presence of standard pollutants
        pollutants_provided = set()
        for item in pollutant_levels:
            if (
                not isinstance(item, dict) or
                "pollutant_type" not in item or
                "concentration" not in item
            ):
                return { "success": False, "error": "Each pollutant_level must have 'pollutant_type' and 'concentration'" }
            pollutants_provided.add(item["pollutant_type"])

        missing_pollutants = standard_pollutants - pollutants_provided
        if missing_pollutants:
            return {
                "success": False,
                "error": f"Missing standard pollutants: {', '.join(sorted(missing_pollutants))}"
            }

        # main_pollutant must match one of the pollutant_types provided
        if main_pollutant not in pollutants_provided:
            return {
                "success": False,
                "error": "main_pollutant must match one of the pollutants in pollutant_levels"
            }

        # Insert AirQualityMeasurement
        self.measurements[measurement_id] = {
            "measurement_id": measurement_id,
            "location_id": location_id,
            "timestamp": timestamp,
            "AQI": AQI,
            "main_pollutant": main_pollutant
        }
        # Insert pollutant levels
        to_insert = []
        for item in pollutant_levels:
            to_insert.append({
                "measurement_id": measurement_id,
                "pollutant_type": item["pollutant_type"],
                "concentration": item["concentration"]
            })
        self.pollutant_levels[measurement_id] = to_insert

        return {
            "success": True,
            "message": f"Air Quality Measurement added for {measurement_id}"
        }

    def update_pollutant_level(self, measurement_id: str, pollutant_type: str, concentration: float) -> dict:
        """
        Update the concentration value for a specific pollutant in a given measurement.

        Args:
            measurement_id (str): The ID of the air quality measurement.
            pollutant_type (str): The pollutant type to update (e.g., "NO2", "PM2.5").
            concentration (float): The new concentration value.

        Returns:
            dict: {
                "success": True,
                "message": "Concentration for <pollutant_type> in measurement <measurement_id> updated."
            }
            or
            {
                "success": False,
                "error": "Measurement not found" | "Pollutant type not found for this measurement"
            }

        Constraints:
            - Measurement ID and pollutant type must exist.
            - Does not recalculate AQI/main_pollutant automatically.
        """
        if measurement_id not in self.pollutant_levels:
            return { "success": False, "error": "Measurement not found" }

        found = False
        for pollutant_info in self.pollutant_levels[measurement_id]:
            if pollutant_info["pollutant_type"] == pollutant_type:
                pollutant_info["concentration"] = concentration
                found = True
                break

        if not found:
            return {
                "success": False,
                "error": "Pollutant type not found for this measurement"
            }
    
        return {
            "success": True,
            "message": f"Concentration for {pollutant_type} in measurement {measurement_id} updated."
        }

    def recalculate_AQI_and_main_pollutant(self, measurement_id: str) -> dict:
        """
        Recalculate the AQI value and identify the main pollutant for a specific measurement
        based on the current pollutant concentrations.

        Args:
            measurement_id (str): The ID of the measurement to update.

        Returns:
            dict:
                Success:
                    {
                        "success": True,
                        "message": "AQI and main pollutant recalculated for measurement <measurement_id>."
                    }
                Failure (not found or missing data):
                    {
                        "success": False,
                        "error": "<reason>"
                    }

        Constraints:
            - measurement_id must exist in measurements and pollutant_levels.
            - Pollutant concentrations for at least one pollutant must be present.
            - AQI and main_pollutant must be updated in self.measurements.
        """
        if measurement_id not in self.measurements:
            return {"success": False, "error": "Measurement not found."}
        if measurement_id not in self.pollutant_levels or not self.pollutant_levels[measurement_id]:
            return {"success": False, "error": "No pollutant levels available to recalculate AQI."}

        # Placeholder: Assume AQI = max concentration, and main_pollutant = pollutant with max concentration.
        levels = self.pollutant_levels[measurement_id]
        max_conc = None
        main_pollutant = None

        for level in levels:
            if max_conc is None or level["concentration"] > max_conc:
                max_conc = level["concentration"]
                main_pollutant = level["pollutant_type"]

        if max_conc is None or main_pollutant is None:
            return {"success": False, "error": "No valid pollutant concentrations for AQI calculation."}

        # Update the measurement record
        self.measurements[measurement_id]["AQI"] = float(max_conc)
        self.measurements[measurement_id]["main_pollutant"] = main_pollutant

        return {
            "success": True,
            "message": f"AQI and main pollutant recalculated for measurement {measurement_id}."
        }

    def delete_air_quality_measurement(self, measurement_id: str) -> dict:
        """
        Remove an Air Quality Measurement and all its associated pollutant level records.

        Args:
            measurement_id (str): Unique identifier for the measurement to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Measurement and associated pollutant records deleted."
            }
            or
            {
                "success": False,
                "error": "Measurement not found."
            }

        Constraints:
            - If the measurement_id does not exist, return an error.
            - Associated pollutant level records for this measurement_id must also be deleted.
        """
        if measurement_id not in self.measurements:
            return { "success": False, "error": "Measurement not found." }

        # Remove measurement
        del self.measurements[measurement_id]

        # Remove pollutant records (if exist)
        if measurement_id in self.pollutant_levels:
            del self.pollutant_levels[measurement_id]

        return {
            "success": True,
            "message": "Measurement and associated pollutant records deleted."
        }

    def add_location(self, location_id: str, city_name: str, country: str, region_coordinate: str) -> dict:
        """
        Register a new city/region as a monitored Location in the system.

        Args:
            location_id (str): Unique identifier for the new location.
            city_name (str): Name of the city or region.
            country (str): Country the location is in.
            region_coordinate (str): Coordinate or descriptor for the region.

        Returns:
            dict: 
              - On success: { "success": True, "message": "Location added: <location_id>" }
              - On failure: { "success": False, "error": <reason> }
    
        Constraints:
            - location_id must be unique (must not exist in self.locations).
            - All fields must be non-empty.
        """
        if not all([location_id, city_name, country, region_coordinate]):
            return { "success": False, "error": "All fields (location_id, city_name, country, region_coordinate) are required." }

        if location_id in self.locations:
            return { "success": False, "error": f"Location ID '{location_id}' already exists." }

        self.locations[location_id] = {
            "location_id": location_id,
            "city_name": city_name,
            "country": country,
            "region_coordinate": region_coordinate
        }
        return { "success": True, "message": f"Location added: {location_id}" }


class AirQualityMonitoringSystem(BaseEnv):
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

    def get_location_by_city_country(self, **kwargs):
        return self._call_inner_tool('get_location_by_city_country', kwargs)

    def list_locations(self, **kwargs):
        return self._call_inner_tool('list_locations', kwargs)

    def get_latest_measurement_for_location(self, **kwargs):
        return self._call_inner_tool('get_latest_measurement_for_location', kwargs)

    def get_measurement_by_id(self, **kwargs):
        return self._call_inner_tool('get_measurement_by_id', kwargs)

    def get_AQI_and_main_pollutant(self, **kwargs):
        return self._call_inner_tool('get_AQI_and_main_pollutant', kwargs)

    def get_pollutant_levels_for_measurement(self, **kwargs):
        return self._call_inner_tool('get_pollutant_levels_for_measurement', kwargs)

    def get_pollutant_concentration(self, **kwargs):
        return self._call_inner_tool('get_pollutant_concentration', kwargs)

    def list_measurements_for_location(self, **kwargs):
        return self._call_inner_tool('list_measurements_for_location', kwargs)

    def add_air_quality_measurement(self, **kwargs):
        return self._call_inner_tool('add_air_quality_measurement', kwargs)

    def update_pollutant_level(self, **kwargs):
        return self._call_inner_tool('update_pollutant_level', kwargs)

    def recalculate_AQI_and_main_pollutant(self, **kwargs):
        return self._call_inner_tool('recalculate_AQI_and_main_pollutant', kwargs)

    def delete_air_quality_measurement(self, **kwargs):
        return self._call_inner_tool('delete_air_quality_measurement', kwargs)

    def add_location(self, **kwargs):
        return self._call_inner_tool('add_location', kwargs)

