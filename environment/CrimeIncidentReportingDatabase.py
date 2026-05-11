# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
from typing import List, Dict
from datetime import datetime
import math
from typing import List, Optional, Dict, Any



class MetadataInfo(TypedDict):
    reported_by: str
    status: str
    narrative_description: str
    case_num: str

class CrimeIncidentInfo(TypedDict):
    incident_id: str
    type: str
    date: str
    time: str
    latitude: float
    longitude: float
    location_description: str
    metadata: MetadataInfo

class _GeneratedEnvImpl:
    def __init__(self):
        # Crime Incidents: {incident_id: CrimeIncidentInfo}
        self.incidents: Dict[str, CrimeIncidentInfo] = {}

        # Constraints:
        # - Each incident must have a unique incident_id (enforced by dict keys)
        # - Each crime incident must have valid latitude and longitude values
        # - Date and time must be properly formatted and associated with the local time zone
        # - Incidents must be associated with at least a minimal type/category (e.g., theft, assault)
        # - All location and date queries should return only those incidents matching the specified parameters

    def get_incident_by_id(self, incident_id: str) -> dict:
        """
        Retrieve full details of a crime incident by its unique incident_id.

        Args:
            incident_id (str): Unique identifier for the crime incident.

        Returns:
            dict: {
                "success": True,
                "data": CrimeIncidentInfo
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The incident_id must exist in the database.
        """
        if incident_id not in self.incidents:
            return {"success": False, "error": "Incident ID not found"}

        return {"success": True, "data": self.incidents[incident_id]}

    def list_all_incidents(self) -> dict:
        """
        Return the complete list of recorded crime incidents (as CrimeIncidentInfo dicts).

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[CrimeIncidentInfo]
            }
            The list may be empty if there are no incidents.

        Constraints:
            - No filtering; return all incidents.
        """
        data = list(self.incidents.values())
        return { "success": True, "data": data }

    def list_incidents_by_type(self, incident_type: str) -> dict:
        """
        Filter and return all crime incidents of the specified type/category.

        Args:
            incident_type (str): The category (e.g., 'theft', 'assault') to filter by.
                The comparison is case-insensitive.

        Returns:
            dict: {
                "success": True,
                "data": List[CrimeIncidentInfo],  # List of matching incident records (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Error description (e.g., invalid type argument)
            }

        Constraints:
            - Type must not be empty.
            - Comparison is case-insensitive for usability.
        """
        if not isinstance(incident_type, str) or not incident_type.strip():
            return {"success": False, "error": "Incident type must be a non-empty string."}

        filtered = [
            incident for incident in self.incidents.values()
            if incident.get("type", "").lower() == incident_type.strip().lower()
        ]
        return {"success": True, "data": filtered}


    def list_incidents_by_date_range(self, start_date: str, end_date: str) -> dict:
        """
        Retrieve all crime incidents that occurred within the specified date range (inclusive).

        Args:
            start_date (str): The starting date (YYYY-MM-DD format, inclusive).
            end_date (str): The ending date (YYYY-MM-DD format, inclusive).

        Returns:
            dict:
                - success (True), data (List[CrimeIncidentInfo]) on success.
                - success (False), error (str) on parsing/validation error.

        Constraints:
            - start_date and end_date must be in YYYY-MM-DD format.
            - start_date must be <= end_date.
            - Only incidents whose 'date' is within [start_date, end_date] (inclusive) are returned.
            - No error for no match: simply return an empty list.
        """
        # Validate date formats
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            return {"success": False, "error": "Invalid date format. Expected YYYY-MM-DD."}

        if start_dt > end_dt:
            return {"success": False, "error": "start_date must be before or equal to end_date."}

        result: List[CrimeIncidentInfo] = []
        for incident in self.incidents.values():
            try:
                incident_dt = datetime.strptime(incident["date"], "%Y-%m-%d")
            except Exception:
                # Skip incidents with malformed date
                continue
            if start_dt <= incident_dt <= end_dt:
                result.append(incident)

        return {"success": True, "data": result}


    def list_incidents_by_location(
        self, 
        latitude: float, 
        longitude: float, 
        radius: Optional[float] = None
    ) -> dict:
        """
        Retrieve all incidents that match specific latitude and longitude coordinates,
        optionally within a given radius (in kilometers).

        Args:
            latitude (float): Reference latitude in decimal degrees (-90 <= lat <= 90).
            longitude (float): Reference longitude in decimal degrees (-180 <= lon <= 180).
            radius (Optional[float]): Search radius in kilometers. If None or <= 0, uses exact match.

        Returns:
            dict: {
                "success": True,
                "data": List[CrimeIncidentInfo],  # All matching incidents (may be empty)
            }
            or
            {
                "success": False,
                "error": str,  # Description of the error
            }

        Constraints:
            - Latitude must be between -90 and 90.
            - Longitude must be between -180 and 180.
            - If radius is provided and > 0, matches any incident within that distance from the reference coordinate.
            - Otherwise, matches only incidents with exact coordinates.
        """
        # Validate latitude and longitude
        if not (-90 <= latitude <= 90):
            return {"success": False, "error": "Invalid latitude value"}
        if not (-180 <= longitude <= 180):
            return {"success": False, "error": "Invalid longitude value"}
        # Validate radius (optional)
        if radius is not None:
            try:
                radius = float(radius)
            except (ValueError, TypeError):
                return {"success": False, "error": "Invalid radius value"}

        def haversine(lat1, lon1, lat2, lon2):
            # Calculate the great-circle distance between two points on the Earth (km)
            R = 6371.0  # Earth radius in kilometers
            phi1 = math.radians(lat1)
            phi2 = math.radians(lat2)
            dphi = math.radians(lat2 - lat1)
            dlambda = math.radians(lon2 - lon1)
            a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            return R * c

        results: List[CrimeIncidentInfo] = []
        if radius is not None and radius > 0:
            # Within radius mode
            for incident in self.incidents.values():
                if not (-90 <= incident['latitude'] <= 90) or not (-180 <= incident['longitude'] <= 180):
                    continue  # skip invalid points
                dist = haversine(latitude, longitude, incident["latitude"], incident["longitude"])
                if dist <= radius:
                    results.append(incident)
        else:
            # Exact match mode
            for incident in self.incidents.values():
                if (
                    abs(incident["latitude"] - latitude) < 1e-8
                    and abs(incident["longitude"] - longitude) < 1e-8
                ):
                    results.append(incident)

        return {"success": True, "data": results}

    def list_incidents_by_location_and_date(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str = None
    ) -> dict:
        """
        Retrieve all incidents that match BOTH the specified location (latitude, longitude)
        AND the date or date range.

        Args:
            latitude (float): The latitude to match.
            longitude (float): The longitude to match.
            start_date (str): The start date (inclusive), format 'YYYY-MM-DD'.
            end_date (str, optional): The end date (inclusive), format 'YYYY-MM-DD'. If None, will match only start_date.

        Returns:
            dict:
                If success:
                    {"success": True, "data": List[CrimeIncidentInfo]}
                If failure (bad input):
                    {"success": False, "error": "..."}
        Constraints:
            - Date format must be 'YYYY-MM-DD'.
            - Latitude and longitude must be floats.
        """
        # Validate latitude and longitude are floats
        if not isinstance(latitude, float) or not isinstance(longitude, float):
            return {"success": False, "error": "Latitude and longitude must be float values"}

        # Simple date format validation (YYYY-MM-DD)
        def valid_date_format(d):
            if not isinstance(d, str):
                return False
            parts = d.split('-')
            return len(parts) == 3 and \
                   all(part.isdigit() for part in parts) and \
                   len(parts[0]) == 4 and len(parts[1]) == 2 and len(parts[2]) == 2

        if not valid_date_format(start_date):
            return {"success": False, "error": "Invalid start_date format, must be YYYY-MM-DD"}

        if end_date is not None:
            if not valid_date_format(end_date):
                return {"success": False, "error": "Invalid end_date format, must be YYYY-MM-DD"}
            if start_date > end_date:
                return {"success": False, "error": "start_date must be before or equal to end_date"}

        # Filtering
        matches = []
        for incident in self.incidents.values():
            if incident["latitude"] == latitude and incident["longitude"] == longitude:
                date = incident["date"]
                if end_date is not None:
                    if start_date <= date <= end_date:
                        matches.append(incident)
                else:
                    if date == start_date:
                        matches.append(incident)

        return {"success": True, "data": matches}

    def get_incident_metadata(self, incident_id: str) -> dict:
        """
        Retrieve the metadata for the specified incident.

        Args:
            incident_id (str): The unique identifier of the incident.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": MetadataInfo
                }
                OR
                {
                    "success": False,
                    "error": str  # Error message if not found.
                }

        Constraints:
            - incident_id must correspond to an existing crime incident.
        """
        incident = self.incidents.get(incident_id)
        if incident is None:
            return { "success": False, "error": "Incident ID not found." }
        return { "success": True, "data": incident["metadata"] }

    def search_incidents(self, filters: dict) -> dict:
        """
        General search function allowing filtering by any combination of:
          - type (str)
          - date (str, or {'from': str, 'to': str})
          - location (latitude/longitude or bounding box {'lat_min': float, 'lat_max': float, 'lon_min': float, 'lon_max': float})
          - location_description (str)
          - metadata fields: reported_by, status, narrative_description, case_num

        Args:
            filters (dict): Dictionary with any above fields as keys or a nested dict for range/bounding queries.

        Returns:
            dict: {
                "success": True,
                "data": List[CrimeIncidentInfo],  # Matching incidents (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # On invalid filter key or malformed filter
            }

        Constraints:
            - All filter keys must be valid field names.
            - All matching incidents are returned.
            - Range queries supported for date and location (if dicts given).
        """

        valid_fields = {
            'type', 'date', 'time', 'latitude', 'longitude', 'location_description'
        }
        valid_metadata = {
            'reported_by', 'status', 'narrative_description', 'case_num'
        }

        # Validate filter keys
        for key in filters:
            if key not in valid_fields and key not in valid_metadata and key not in ['latitude_range', 'longitude_range', 'date_range', 'location_bbox']:
                return {"success": False, "error": f"Invalid filter key: {key}"}

        result = []
        for inc in self.incidents.values():
            match = True
            for key, value in filters.items():
                # Incident main fields
                if key in valid_fields:
                    if key in ['latitude', 'longitude']:
                        # For lat/lon we expect numeric equality, unless using range filter
                        if inc[key] != value:
                            match = False
                            break
                    elif key == 'date':
                        if isinstance(value, dict):
                            dfrom = value.get('from')
                            dto = value.get('to')
                            if dfrom is not None and inc['date'] < dfrom:
                                match = False
                                break
                            if dto is not None and inc['date'] > dto:
                                match = False
                                break
                        else:
                            if inc[key] != value:
                                match = False
                                break
                    elif key == 'location_description':
                        incident_location = inc.get('location_description', '')
                        if isinstance(value, dict):
                            contains = value.get('contains')
                            exact = value.get('exact')
                            if contains is not None:
                                if not isinstance(contains, str):
                                    return {"success": False, "error": "location_description.contains must be a string"}
                                if contains.lower() not in incident_location.lower():
                                    match = False
                                    break
                            elif exact is not None:
                                if incident_location != exact:
                                    match = False
                                    break
                            else:
                                return {
                                    "success": False,
                                    "error": "location_description dict filters must use 'contains' or 'exact'",
                                }
                        else:
                            if not isinstance(value, str):
                                return {"success": False, "error": "location_description filter must be a string or dict"}
                            if value.lower() not in incident_location.lower():
                                match = False
                                break
                    else:
                        if inc[key] != value:
                            match = False
                            break
                # Metadata fields
                elif key in valid_metadata:
                    if inc['metadata'].get(key) != value:
                        match = False
                        break
                # Date range
                elif key == 'date_range':
                    dfrom = value.get('from')
                    dto   = value.get('to')
                    if dfrom is not None and inc['date'] < dfrom:
                        match = False
                        break
                    if dto is not None and inc['date'] > dto:
                        match = False
                        break
                # Latitude range
                elif key == 'latitude_range':
                    vmin = value.get('min')
                    vmax = value.get('max')
                    if vmin is not None and inc['latitude'] < vmin:
                        match = False
                        break
                    if vmax is not None and inc['latitude'] > vmax:
                        match = False
                        break
                # Longitude range
                elif key == 'longitude_range':
                    vmin = value.get('min')
                    vmax = value.get('max')
                    if vmin is not None and inc['longitude'] < vmin:
                        match = False
                        break
                    if vmax is not None and inc['longitude'] > vmax:
                        match = False
                        break
                # Bounding box
                elif key == 'location_bbox':
                    lat_min = value.get('lat_min')
                    lat_max = value.get('lat_max')
                    lon_min = value.get('lon_min')
                    lon_max = value.get('lon_max')
                    if (
                        (lat_min is not None and inc['latitude'] < lat_min) or
                        (lat_max is not None and inc['latitude'] > lat_max) or
                        (lon_min is not None and inc['longitude'] < lon_min) or
                        (lon_max is not None and inc['longitude'] > lon_max)
                    ):
                        match = False
                        break
                else:
                    return {"success": False, "error": f"Invalid or unsupported filter key: {key}"}
            if match:
                result.append(inc)

        return {"success": True, "data": result}

    def add_incident(self, incident_info: dict) -> dict:
        """
        Add a new crime incident to the database, enforcing unique id and data validation constraints.

        Args:
            incident_info (dict): Should match CrimeIncidentInfo TypedDict, e.g.
                {
                    'incident_id': str,
                    'type': str,
                    'date': str,
                    'time': str,
                    'latitude': float,
                    'longitude': float,
                    'location_description': str,
                    'metadata': {
                        'reported_by': str,
                        'status': str,
                        'narrative_description': str,
                        'case_num': str
                    }
                }

        Returns:
            dict: {
                "success": True,
                "message": "Incident <incident_id> added successfully."
            } or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - incident_id must be unique.
            - latitude and longitude must be within valid range.
            - type must be provided and non-empty.
            - date and time must be provided and non-empty.
        """
        # Required fields
        required_fields = [
            "incident_id", "type", "date", "time", "latitude", "longitude", "location_description", "metadata"
        ]
        metadata_required_fields = ["reported_by", "status", "narrative_description", "case_num"]

        # Check for missing fields
        for field in required_fields:
            if field not in incident_info:
                return { "success": False, "error": f"Missing required field: '{field}'" }

        # Uniqueness
        incident_id = incident_info["incident_id"]
        if incident_id in self.incidents:
            return { "success": False, "error": f"Incident ID '{incident_id}' already exists." }

        # Type/category
        if not incident_info["type"] or not isinstance(incident_info["type"], str):
            return { "success": False, "error": "Incident 'type' must be provided and non-empty." }

        # Date/time
        if not incident_info["date"] or not isinstance(incident_info["date"], str):
            return { "success": False, "error": "Incident 'date' must be provided and non-empty." }
        if not incident_info["time"] or not isinstance(incident_info["time"], str):
            return { "success": False, "error": "Incident 'time' must be provided and non-empty." }

        # Latitude/Longitude
        lat = incident_info["latitude"]
        lon = incident_info["longitude"]
        if not (isinstance(lat, (float, int)) and -90 <= lat <= 90):
            return { "success": False, "error": "Latitude must be a number between -90 and 90." }
        if not (isinstance(lon, (float, int)) and -180 <= lon <= 180):
            return { "success": False, "error": "Longitude must be a number between -180 and 180." }

        # Metadata
        metadata = incident_info.get("metadata")
        if not isinstance(metadata, dict):
            return { "success": False, "error": "Metadata must be a dictionary." }
        for field in metadata_required_fields:
            if field not in metadata:
                return { "success": False, "error": f"Missing metadata field: '{field}'" }

        # Add incident
        self.incidents[incident_id] = incident_info

        return { "success": True, "message": f"Incident {incident_id} added successfully." }

    def update_incident(
        self,
        incident_id: str,
        type: str = None,
        date: str = None,
        time: str = None,
        latitude: float = None,
        longitude: float = None,
        location_description: str = None,
        metadata: dict = None
    ) -> dict:
        """
        Modify the details of an existing incident given its incident_id.
        All fields are optional except incident_id; only those provided will be updated.
    
        Args:
            incident_id (str): Unique id for the incident to be modified.
            type (str, optional): Updated crime type. Must not be empty if provided.
            date (str, optional): Updated date ("YYYY-MM-DD" recommended).
            time (str, optional): Updated time ("HH:MM" etc.).
            latitude (float, optional): Updated latitude (-90 <= latitude <= 90).
            longitude (float, optional): Updated longitude (-180 <= longitude <= 180).
            location_description (str, optional): Updated location description.
            metadata (dict, optional): Dict with any of ("reported_by", "status", "narrative_description", "case_num").
    
        Returns:
            dict: { "success": True, "message": "Incident updated successfully" }
                  or
                  { "success": False, "error": "<reason>" }
        Constraints:
            - incident_id must exist.
            - If type is provided, must be non-empty string.
            - If latitude/longitude are provided, must be valid floats in range.
            - If metadata is provided, must only contain allowed keys.
        """
        # Check incident exists
        if incident_id not in self.incidents:
            return { "success": False, "error": "Incident does not exist." }
        original_incident = self.incidents[incident_id]
        incident = copy.deepcopy(original_incident)
        updated = False
    
        # Update main attributes
        if type is not None:
            if not isinstance(type, str) or not type.strip():
                return { "success": False, "error": "Type must be a non-empty string." }
            incident["type"] = type
            updated = True

        if date is not None:
            # Light validation (format could be improved)
            if not isinstance(date, str) or not date.strip():
                return { "success": False, "error": "Date must be a non-empty string." }
            incident["date"] = date
            updated = True

        if time is not None:
            if not isinstance(time, str) or not time.strip():
                return { "success": False, "error": "Time must be a non-empty string." }
            incident["time"] = time
            updated = True

        if latitude is not None:
            try:
                latf = float(latitude)
            except (TypeError, ValueError):
                return { "success": False, "error": "Latitude must be a float." }
            if latf < -90 or latf > 90:
                return { "success": False, "error": "Latitude out of valid range (-90 to 90)." }
            incident["latitude"] = latf
            updated = True

        if longitude is not None:
            try:
                lonf = float(longitude)
            except (TypeError, ValueError):
                return { "success": False, "error": "Longitude must be a float." }
            if lonf < -180 or lonf > 180:
                return { "success": False, "error": "Longitude out of valid range (-180 to 180)." }
            incident["longitude"] = lonf
            updated = True

        if location_description is not None:
            if not isinstance(location_description, str):
                return { "success": False, "error": "Location description must be a string." }
            incident["location_description"] = location_description
            updated = True

        # Update metadata subfields
        if metadata is not None:
            if not isinstance(metadata, dict):
                return { "success": False, "error": "Metadata must be a dictionary." }
            allowed_meta_keys = {"reported_by", "status", "narrative_description", "case_num"}
            for key, value in metadata.items():
                if key not in allowed_meta_keys:
                    if key not in incident["metadata"]:
                        return { "success": False, "error": f"Invalid metadata field: {key}" }
                # All metadata values are expected to be strings
                if not isinstance(value, str):
                    return { "success": False, "error": f"Metadata field '{key}' must be a string." }
                incident["metadata"][key] = value
                updated = True

        if not updated:
            return { "success": False, "error": "No valid fields specified to update." }
        self.incidents[incident_id] = incident
        return { "success": True, "message": "Incident updated successfully" }

    def delete_incident(self, incident_id: str) -> dict:
        """
        Remove a crime incident from the database by incident_id.

        Args:
            incident_id (str): Unique identifier of the crime incident to remove.

        Returns:
            dict:
                Success: { "success": True, "message": "Incident <incident_id> deleted." }
                Failure: { "success": False, "error": "Incident not found." }

        Constraints:
            - The given incident_id must exist in the database.
            - Removes the incident from the incident list entirely.
        """
        if incident_id not in self.incidents:
            return { "success": False, "error": "Incident not found." }

        del self.incidents[incident_id]
        return { "success": True, "message": f"Incident {incident_id} deleted." }

    def update_incident_metadata(
        self,
        incident_id: str,
        status: str = None,
        narrative_description: str = None,
        reported_by: str = None,
        case_num: str = None
    ) -> dict:
        """
        Edit only the metadata section (status, narrative, reporter info, case number) for an existing incident.

        Args:
            incident_id (str): The ID of the incident to update.
            status (str, optional): New status value.
            narrative_description (str, optional): New narrative description.
            reported_by (str, optional): New reporter info.
            case_num (str, optional): New case number.

        Returns:
            dict: {
                "success": True,
                "message": "Incident metadata updated successfully."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Only metadata fields are updated, and only for an existing incident.
            - No operation if no field is supplied, but counted as success (no-op).
        """
        incident = self.incidents.get(incident_id)
        if not incident:
            return { "success": False, "error": "Incident not found" }

        metadata = incident.get("metadata", {})
        updated = False

        if status is not None:
            metadata["status"] = status
            updated = True
        if narrative_description is not None:
            metadata["narrative_description"] = narrative_description
            updated = True
        if reported_by is not None:
            metadata["reported_by"] = reported_by
            updated = True
        if case_num is not None:
            metadata["case_num"] = case_num
            updated = True

        incident["metadata"] = metadata
        self.incidents[incident_id] = incident

        return {
            "success": True,
            "message": "Incident metadata updated successfully." if updated else "No metadata fields were changed."
        }


class CrimeIncidentReportingDatabase(BaseEnv):
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

    def get_incident_by_id(self, **kwargs):
        return self._call_inner_tool('get_incident_by_id', kwargs)

    def list_all_incidents(self, **kwargs):
        return self._call_inner_tool('list_all_incidents', kwargs)

    def list_incidents_by_type(self, **kwargs):
        return self._call_inner_tool('list_incidents_by_type', kwargs)

    def list_incidents_by_date_range(self, **kwargs):
        return self._call_inner_tool('list_incidents_by_date_range', kwargs)

    def list_incidents_by_location(self, **kwargs):
        return self._call_inner_tool('list_incidents_by_location', kwargs)

    def list_incidents_by_location_and_date(self, **kwargs):
        return self._call_inner_tool('list_incidents_by_location_and_date', kwargs)

    def get_incident_metadata(self, **kwargs):
        return self._call_inner_tool('get_incident_metadata', kwargs)

    def search_incidents(self, **kwargs):
        return self._call_inner_tool('search_incidents', kwargs)

    def add_incident(self, **kwargs):
        return self._call_inner_tool('add_incident', kwargs)

    def update_incident(self, **kwargs):
        return self._call_inner_tool('update_incident', kwargs)

    def delete_incident(self, **kwargs):
        return self._call_inner_tool('delete_incident', kwargs)

    def update_incident_metadata(self, **kwargs):
        return self._call_inner_tool('update_incident_metadata', kwargs)
