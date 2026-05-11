# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, Any, TypedDict
import math
from typing import List, Optional, Dict, Any
from datetime import datetime
from datetime import datetime, timezone
import time



class TechnicalSpecifications(TypedDict, total=False):
    # Can be extended. Example fields:
    connector_types: list
    charging_power_kw: float
    protocol: str

class ChargingStationInfo(TypedDict):
    station_id: str
    name: str
    latitude: float
    longitude: float
    address: str
    operator_id: str
    capacity: int
    technical_specifications: TechnicalSpecifications
    status: str
    last_updated: str

class OperatorInfo(TypedDict):
    operator_id: str
    name: str
    contact_info: str
    network_name: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment representing the registry of EV charging stations and their operators.
        """

        # Charging stations: {station_id: ChargingStationInfo}
        # Attributes: station_id, name, latitude, longitude, address, operator_id, capacity, technical_specifications, status, last_updated
        self.charging_stations: Dict[str, ChargingStationInfo] = {}

        # Operators: {operator_id: OperatorInfo}
        # Attributes: operator_id, name, contact_info, network_name
        self.operators: Dict[str, OperatorInfo] = {}

        # Constraints:
        # - Each ChargingStation must have a unique station_id.
        # - Latitude and longitude must be valid geographic coordinates.
        # - Every ChargingStation must reference a valid Operator.
        # - Technical specifications should follow standardized formats (see TechnicalSpecifications).
        # - Capacity should be a non-negative integer.
        # - Real-time updates must preserve data integrity (e.g., no duplicate geographic locations unless intentional).
        # - Status must be from a controlled vocabulary (e.g., 'active', 'inactive', 'maintenance').

    def get_charging_station_by_id(self, station_id: str) -> dict:
        """
        Retrieve the complete details of a charging station using its unique station_id.

        Args:
            station_id (str): The unique identifier of the charging station.

        Returns:
            dict:
                - If found: {"success": True, "data": ChargingStationInfo}
                - If not found: {"success": False, "error": "Charging station with this ID does not exist."}

        Constraints:
            - Each station_id must be unique (guaranteed by registry design).
        """
        station = self.charging_stations.get(station_id)
        if station is None:
            return {"success": False, "error": "Charging station with this ID does not exist."}
        return {"success": True, "data": station}


    def search_charging_stations_by_coordinates(
        self, 
        latitude: float, 
        longitude: float, 
        radius_km: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Find charging stations by exact latitude/longitude or within a geographic radius.

        Args:
            latitude (float): Latitude of the point to search (must be between -90 and 90).
            longitude (float): Longitude of the point to search (must be between -180 and 180).
            radius_km (Optional[float]): Optional. Radius (in kilometers) to search for stations.
                If provided and >=0, finds all stations within the radius.
                If None, only stations with exact coordinates will be matched.

        Returns:
            dict: {
                "success": True,
                "data": List[ChargingStationInfo],  # May be empty list if no match.
            }
            or
            {
                "success": False,
                "error": str  # Description of error
            }

        Constraints:
            - Latitude must be in [-90, 90]; longitude in [-180, 180].
            - If radius_km is provided, it must be non-negative.
        """

        # Validate coordinates
        if not (-90.0 <= latitude <= 90.0):
            return {"success": False, "error": "Invalid latitude. Must be between -90 and 90."}
        if not (-180.0 <= longitude <= 180.0):
            return {"success": False, "error": "Invalid longitude. Must be between -180 and 180."}
        if radius_km is not None and radius_km < 0:
            return {"success": False, "error": "radius_km must be a non-negative number if provided."}

        results: List[ChargingStationInfo] = []

        def haversine(lat1, lon1, lat2, lon2):
            # Returns distance in kilometers between two coordinate points.
            R = 6371.0  # Radius of earth in kilometers.
            phi1 = math.radians(lat1)
            phi2 = math.radians(lat2)
            delta_phi = math.radians(lat2 - lat1)
            delta_lambda = math.radians(lon2 - lon1)
            a = (
                math.sin(delta_phi / 2) ** 2 +
                math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
            )
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            return R * c

        for station in self.charging_stations.values():
            st_lat = station.get("latitude")
            st_lon = station.get("longitude")
            if radius_km is not None:
                distance = haversine(latitude, longitude, st_lat, st_lon)
                if distance <= radius_km:
                    results.append(station)
            else:
                if abs(st_lat - latitude) < 1e-7 and abs(st_lon - longitude) < 1e-7:
                    results.append(station)

        return {"success": True, "data": results}

    def list_charging_stations_by_operator(self, operator_id: str) -> dict:
        """
        Retrieve all charging stations managed by the specified operator.

        Args:
            operator_id (str): Unique identifier of the operator.

        Returns:
            dict: {
                "success": True,
                "data": List[ChargingStationInfo]  # Charging stations managed by the operator (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Explanation (e.g., operator does not exist)
            }
        Constraints:
            - operator_id must reference a valid Operator in the registry.
        """
        if operator_id not in self.operators:
            return { "success": False, "error": "Operator does not exist" }

        result = [
            station_info for station_info in self.charging_stations.values()
            if station_info["operator_id"] == operator_id
        ]
        return { "success": True, "data": result }

    def get_charging_station_status(self, station_id: str) -> dict:
        """
        Query the operational status of a charging station.

        Args:
            station_id (str): The unique identifier for the charging station.

        Returns:
            dict:
                success: True and data dict with station_id and status if found,
                         or
                success: False and error message if not found.

        Constraints:
            - station_id must exist in the registry.
            - Only queries the status; result comes from the controlled vocabulary set in the data.
        """
        if not station_id or not isinstance(station_id, str):
            return { "success": False, "error": "Invalid station_id" }

        station = self.charging_stations.get(station_id)
        if not station:
            return { "success": False, "error": "Charging station not found" }

        return {
            "success": True,
            "data": {
                "station_id": station_id,
                "status": station["status"]
            }
        }

    def get_technical_specifications(self, station_id: str) -> dict:
        """
        Retrieve the technical specifications of the specified charging station.

        Args:
            station_id (str): The unique identifier of the charging station.

        Returns:
            dict: {
                "success": True,
                "data": TechnicalSpecifications  # May be empty dict if no specs.
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g. charging station not found
            }
    
        Constraints:
            - The charging station referenced by station_id must exist in the registry.
        """
        station_info = self.charging_stations.get(station_id)
        if station_info is None:
            return { "success": False, "error": "Charging station not found" }
    
        technical_specs = station_info.get("technical_specifications", {})
        return { "success": True, "data": technical_specs }

    def get_operator_info(self, operator_id: str) -> dict:
        """
        Retrieve full information about an operator using operator_id.

        Args:
            operator_id (str): The unique identifier of the operator.

        Returns:
            dict: 
              - On success: { "success": True, "data": OperatorInfo }
              - On failure: { "success": False, "error": "Operator not found" }

        Constraints:
            - The operator_id must exist in the operator registry.
        """
        operator_info = self.operators.get(operator_id)
        if not operator_info:
            return { "success": False, "error": "Operator not found" }
        return { "success": True, "data": operator_info }

    def list_all_charging_stations(self) -> dict:
        """
        Retrieve all charging stations currently registered in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[ChargingStationInfo]  # List with all charging stations (empty if none)
            }
        """
        all_stations = list(self.charging_stations.values())
        return {"success": True, "data": all_stations}

    def validate_station_operator_reference(self, station_id: str) -> dict:
        """
        Verify that the given charging station's operator_id corresponds to a valid operator.

        Args:
            station_id (str): The unique identifier for the charging station.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "station_id": str,
                    "operator_id": str,
                    "operator_valid": bool,
                    "operator_info": OperatorInfo | None,
                }
            }
            or
            {
                "success": False,
                "error": str  # Description of what went wrong
            }

        Constraints:
            - The charging station must exist.
            - The operator_id must exist among operators for the reference to be valid.
        """
        cs = self.charging_stations.get(station_id)
        if not cs:
            return {"success": False, "error": "Charging station does not exist"}

        operator_id = cs.get("operator_id")
        operator_info = self.operators.get(operator_id)
        if operator_info:
            return {
                "success": True,
                "data": {
                    "station_id": station_id,
                    "operator_id": operator_id,
                    "operator_valid": True,
                    "operator_info": operator_info,
                }
            }
        else:
            return {
                "success": True,
                "data": {
                    "station_id": station_id,
                    "operator_id": operator_id,
                    "operator_valid": False,
                    "operator_info": None,
                }
            }

    def check_coordinates_validity(self, latitude: Any, longitude: Any) -> dict:
        """
        Validate if provided latitude/longitude values are syntactically and geographically correct.

        Args:
            latitude (Any): The latitude value to validate.
            longitude (Any): The longitude value to validate.

        Returns:
            dict: 
              - {"success": True, "valid": True} if both are valid.
              - {"success": True, "valid": False, "error": "..."} if syntax or range is invalid.
              - {"success": False, "error": "..."} if unable to parse as float.

        Constraints:
            - Latitude must be within [-90, 90].
            - Longitude must be within [-180, 180].
            - Both values must be numbers.
        """

        # Check types and parse as float if needed
        try:
            lat = float(latitude)
            lon = float(longitude)
        except (TypeError, ValueError):
            return {"success": False, "error": "Latitude/Longitude must be numbers"}

        # Validate ranges
        if not (-90.0 <= lat <= 90.0):
            return {
                "success": True,
                "valid": False,
                "error": "Latitude must be in range [-90, 90]"
            }
        if not (-180.0 <= lon <= 180.0):
            return {
                "success": True,
                "valid": False,
                "error": "Longitude must be in range [-180, 180]"
            }

        return {"success": True, "valid": True}

    def add_charging_station(
        self,
        station_id: str,
        name: str,
        latitude: float,
        longitude: float,
        address: str,
        operator_id: str,
        capacity: int,
        technical_specifications: dict,
        status: str,
        last_updated: str
    ) -> dict:
        """
        Add a new charging station entry to the registry.

        Args:
            station_id (str): Unique identifier for the station.
            name (str): Name of the charging station.
            latitude (float): Station latitude, must be between -90 and 90.
            longitude (float): Station longitude, must be between -180 and 180.
            address (str): Physical address.
            operator_id (str): ID of the operator (must exist).
            capacity (int): Number of available charging points, non-negative.
            technical_specifications (dict): Specs describing hardware, protocol, etc.
            status (str): Operational status ('active', 'inactive', or 'maintenance').
            last_updated (str): Timestamp in ISO 8601 or standard string format.

        Returns:
            dict: { "success": True, "message": "..."}
                  { "success": False, "error": "..."}
    
        Constraints:
            - station_id must be unique.
            - latitude & longitude must be within valid ranges.
            - capacity >= 0.
            - operator_id must be present in operators.
            - status must be one of ['active', 'inactive', 'maintenance'].
        """
        controlled_status = {'active', 'inactive', 'maintenance'}

        if station_id in self.charging_stations:
            return { "success": False, "error": "station_id already exists." }
        if not (-90.0 <= latitude <= 90.0):
            return { "success": False, "error": "Invalid latitude (must be -90 to 90)." }
        if not (-180.0 <= longitude <= 180.0):
            return { "success": False, "error": "Invalid longitude (must be -180 to 180)." }
        if capacity < 0:
            return { "success": False, "error": "Capacity must be non-negative." }
        if operator_id not in self.operators:
            return { "success": False, "error": "Operator_id does not exist." }
        if status not in controlled_status:
            return { "success": False, "error": "Status must be one of: active, inactive, maintenance." }
        if not isinstance(technical_specifications, dict):
            return { "success": False, "error": "Technical specifications must be a dict." }

        # Additional minimal check for technical_specifications
        # (e.g., must have at least connector_types key as a list, not enforced unless specified)

        station_info: ChargingStationInfo = {
            "station_id": station_id,
            "name": name,
            "latitude": latitude,
            "longitude": longitude,
            "address": address,
            "operator_id": operator_id,
            "capacity": capacity,
            "technical_specifications": technical_specifications,
            "status": status,
            "last_updated": last_updated
        }
        self.charging_stations[station_id] = station_info

        return { "success": True, "message": "Charging station added successfully." }

    def update_charging_station_details(
        self,
        station_id: str,
        name: str = None,
        latitude: float = None,
        longitude: float = None,
        address: str = None,
        operator_id: str = None,
        capacity: int = None,
        technical_specifications: dict = None,
        status: str = None
    ) -> dict:
        """
        Modify details of an existing charging station specified by station_id.

        Args:
            station_id (str): Unique identifier for the charging station.
            name (str, optional): New station name.
            latitude (float, optional): New latitude (-90 to 90).
            longitude (float, optional): New longitude (-180 to 180).
            address (str, optional): New address.
            operator_id (str, optional): ID of new operator (must exist).
            capacity (int, optional): New capacity (non-negative).
            technical_specifications (dict, optional): New technical specs dict.
            status (str, optional): New operational status ('active', 'inactive', 'maintenance').

        Returns:
            dict: {
                "success": True,
                "message": "Charging station details updated successfully."
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - station_id must exist.
            - latitude and longitude must be within valid ranges if provided.
            - status must be one of allowed values.
            - capacity, if provided, must be non-negative integer.
            - operator_id, if provided, must already exist.
            - technical_specifications, if provided, must be a dict.
        """
        allowed_status = {"active", "inactive", "maintenance"}

        # Check if station exists
        if station_id not in self.charging_stations:
            return {"success": False, "error": "Charging station does not exist."}

        station = self.charging_stations[station_id]
        updated = False

        if name is not None:
            station["name"] = name
            updated = True

        if latitude is not None:
            if not isinstance(latitude, (float, int)):
                return {"success": False, "error": "Latitude must be a number."}
            if not (-90 <= latitude <= 90):
                return {"success": False, "error": "Latitude must be between -90 and 90."}
            station["latitude"] = float(latitude)
            updated = True

        if longitude is not None:
            if not isinstance(longitude, (float, int)):
                return {"success": False, "error": "Longitude must be a number."}
            if not (-180 <= longitude <= 180):
                return {"success": False, "error": "Longitude must be between -180 and 180."}
            station["longitude"] = float(longitude)
            updated = True

        if address is not None:
            station["address"] = address
            updated = True

        if operator_id is not None:
            if operator_id not in self.operators:
                return {"success": False, "error": "Referenced operator does not exist."}
            station["operator_id"] = operator_id
            updated = True

        if capacity is not None:
            if not isinstance(capacity, int) or capacity < 0:
                return {"success": False, "error": "Capacity must be a non-negative integer."}
            station["capacity"] = capacity
            updated = True

        if technical_specifications is not None:
            if not isinstance(technical_specifications, dict):
                return {"success": False, "error": "Technical specifications must be a dict."}
            station["technical_specifications"] = technical_specifications
            updated = True

        if status is not None:
            if status not in allowed_status:
                return {"success": False, "error": "Invalid status value."}
            station["status"] = status
            updated = True

        if updated:
            # Update last_updated timestamp (here use an ISO8601 string; in real code use datetime.now().isoformat())
            station["last_updated"] = datetime.utcnow().isoformat() + "Z"

        return {
            "success": True,
            "message": "Charging station details updated successfully."
        }

    def delete_charging_station(self, station_id: str) -> dict:
        """
        Remove a charging station from the registry.

        Args:
            station_id (str): The unique identifier of the charging station to remove.

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "message": "Charging station {station_id} deleted from registry."
                }
                On failure: {
                    "success": False,
                    "error": "Charging station not found."
                }

        Constraints:
            - The station_id must exist in the registry.
        """
        if station_id not in self.charging_stations:
            return { "success": False, "error": "Charging station not found." }
        del self.charging_stations[station_id]
        return { "success": True, "message": f"Charging station {station_id} deleted from registry." }

    def add_operator(self, operator_id: str, name: str, contact_info: str, network_name: str) -> dict:
        """
        Add a new operator to the registry.

        Args:
            operator_id (str): Unique identifier for the operator.
            name (str): Operator's name.
            contact_info (str): Contact information for the operator.
            network_name (str): Name of the operator's network.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Operator added successfully."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "<reason>"
                    }

        Constraints:
            - operator_id must be unique (not already in the registry).
            - All fields must be non-empty.
        """
        if not operator_id or not name or not contact_info or not network_name:
            return { "success": False, "error": "All fields must be non-empty." }

        if operator_id in self.operators:
            return { "success": False, "error": "Operator ID already exists." }

        self.operators[operator_id] = {
            "operator_id": operator_id,
            "name": name,
            "contact_info": contact_info,
            "network_name": network_name,
        }
        return { "success": True, "message": "Operator added successfully." }

    def update_operator_info(
        self,
        operator_id: str,
        name: str = None,
        contact_info: str = None,
        network_name: str = None
    ) -> dict:
        """
        Modify the information for a registered operator.

        Args:
            operator_id (str): ID of the operator to update.
            name (str, optional): New name for the operator.
            contact_info (str, optional): New contact info.
            network_name (str, optional): New network name.

        Returns:
            dict: {
                "success": True,
                "message": "Operator info for <id> updated."
            }
            OR
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - operator_id must exist in the registry.
            - At least one field to update must be provided.
            - Updated fields must be non-empty strings (if given).
        """
        if operator_id not in self.operators:
            return {"success": False, "error": "Operator does not exist"}

        update_fields = {}
        if name is not None:
            if not isinstance(name, str) or not name.strip():
                return {"success": False, "error": "Invalid operator name"}
            update_fields["name"] = name.strip()
        if contact_info is not None:
            if not isinstance(contact_info, str) or not contact_info.strip():
                return {"success": False, "error": "Invalid contact_info"}
            update_fields["contact_info"] = contact_info.strip()
        if network_name is not None:
            if not isinstance(network_name, str) or not network_name.strip():
                return {"success": False, "error": "Invalid network_name"}
            update_fields["network_name"] = network_name.strip()

        if not update_fields:
            return {"success": False, "error": "No information to update"}

        self.operators[operator_id].update(update_fields)

        return {
            "success": True,
            "message": f"Operator info for {operator_id} updated."
        }

    def bulk_import_stations(self, stations: list[dict]) -> dict:
        """
        Add or update multiple charging station entries at once, performing batch validation. 
        The operation is atomic: no station will be changed unless all entries pass validation.

        Args:
            stations (list[dict]): List of ChargingStationInfo dictionaries to import (add or update).

        Returns:
            dict:
                On success: 
                    {
                        "success": True,
                        "message": "<N> stations imported/updated successfully"
                    }
                On failure (no stations modified):
                    {
                        "success": False,
                        "error": [
                            {
                                "station_id": <station_id or '(missing)'>,
                                "issues": [ ... list of error messages ... ]
                            },
                            ...
                        ]
                    }

        Constraints:
          - No duplicate station_id in the input.
          - Each station must have:
              - valid unique station_id
              - latitude in [-90, 90]
              - longitude in [-180, 180]
              - existing operator_id
              - status in {'active', 'inactive', 'maintenance'}
              - non-negative integer capacity
        """
        required_status = {'active', 'inactive', 'maintenance'}
        seen_ids = set()
        errors = []

        # Batch pre-validation
        for idx, station in enumerate(stations):
            issues = []
            sid = station.get("station_id")
            lat = station.get("latitude")
            lon = station.get("longitude")
            opid = station.get("operator_id")
            capacity = station.get("capacity")
            status = station.get("status")

            # Check station_id presence and uniqueness (in batch)
            if not sid or not isinstance(sid, str):
                issues.append("Missing or invalid 'station_id'")
            elif sid in seen_ids:
                issues.append(f"Duplicate 'station_id' in input batch: {sid}")
            else:
                seen_ids.add(sid)

            # Latitude check
            try:
                if not (isinstance(lat, (int, float)) and -90.0 <= float(lat) <= 90.0):
                    issues.append("Latitude must be in [-90.0, 90.0]")
            except Exception:
                issues.append("Latitude must be a valid float")

            # Longitude check
            try:
                if not (isinstance(lon, (int, float)) and -180.0 <= float(lon) <= 180.0):
                    issues.append("Longitude must be in [-180.0, 180.0]")
            except Exception:
                issues.append("Longitude must be a valid float")

            # Operator existence
            if not opid or not isinstance(opid, str) or opid not in self.operators:
                issues.append("operator_id missing or does not reference a valid Operator")

            # Status vocabulary
            if not status or status not in required_status:
                issues.append(f"Invalid status: must be one of {sorted(required_status)}")

            # Capacity check
            if not isinstance(capacity, int) or capacity < 0:
                issues.append("Capacity must be a non-negative integer")

            # (Optionally validate technical_specifications structure)
            # Could add additional field checks here if desired

            if issues:
                errors.append({"station_id": sid or "(missing)", "issues": issues})

        if errors:
            return {"success": False, "error": errors}

        # If all valid: apply state changes (add/update in registry)
        for station in stations:
            sid = station["station_id"]
            # Insert or update (upsert) by station_id
            self.charging_stations[sid] = station

        return {
            "success": True,
            "message": f"{len(stations)} stations imported/updated successfully"
        }

    def update_charging_station_status(self, station_id: str, new_status: str) -> dict:
        """
        Change the status of a charging station to a new allowed value ('active', 'maintenance', 'inactive').

        Args:
            station_id (str): The unique ID of the charging station to update.
            new_status (str): The new status to set. Must be one of 'active', 'inactive', 'maintenance'.

        Returns:
            dict:
                - On success: { "success": True, "message": "Station status updated." }
                - On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - Station must exist in the registry.
            - new_status must be a value from the allowed controlled vocabulary.
            - last_updated field is set to the current time in ISO format.
        """
        allowed_statuses = {"active", "inactive", "maintenance"}
        if station_id not in self.charging_stations:
            return { "success": False, "error": "Charging station does not exist." }
        if new_status not in allowed_statuses:
            return { "success": False, "error": f"Invalid status. Must be one of {allowed_statuses}." }

        self.charging_stations[station_id]["status"] = new_status
        self.charging_stations[station_id]["last_updated"] = datetime.now(timezone.utc).isoformat()

        return { "success": True, "message": "Station status updated." }


    def correct_station_coordinates(
        self,
        station_id: str,
        new_latitude: float,
        new_longitude: float,
        allow_duplicate_location: bool = False
    ) -> dict:
        """
        Adjust latitude/longitude for an existing station, ensuring new values are valid and do not conflict unless explicitly allowed.

        Args:
            station_id (str): The ID of the charging station to update.
            new_latitude (float): The new latitude (must be between -90 and 90).
            new_longitude (float): The new longitude (must be between -180 and 180).
            allow_duplicate_location (bool): If True, allows updating to coordinates already used by another station (default: False).

        Returns:
            dict: 
                - On success: { "success": True, "message": "Coordinates updated for station <station_id>." }
                - On error: { "success": False, "error": "reason" }
    
        Constraints:
            - The station_id must exist in the registry.
            - Latitude must be between -90 and 90.
            - Longitude must be between -180 and 180.
            - If allow_duplicate_location is False, cannot duplicate coordinates of another station.
            - On update, 'last_updated' will be set to current ISO timestamp.
        """
        # Validate station exists
        station = self.charging_stations.get(station_id)
        if not station:
            return {"success": False, "error": f"Charging station with ID '{station_id}' does not exist."}

        # Validate coordinates
        if not (-90.0 <= new_latitude <= 90.0):
            return {"success": False, "error": "Latitude must be between -90 and 90."}
        if not (-180.0 <= new_longitude <= 180.0):
            return {"success": False, "error": "Longitude must be between -180 and 180."}

        # Check for coordinate duplication
        if not allow_duplicate_location:
            for other_id, other_station in self.charging_stations.items():
                if other_id != station_id:
                    if (
                        other_station["latitude"] == new_latitude and
                        other_station["longitude"] == new_longitude
                    ):
                        return {
                            "success": False,
                            "error": f"Coordinates ({new_latitude}, {new_longitude}) are already used by station '{other_id}'."
                        }

        # Perform update
        station["latitude"] = new_latitude
        station["longitude"] = new_longitude
        station["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        return {
            "success": True,
            "message": f"Coordinates updated for station {station_id}."
        }


class EVChargingStationRegistry(BaseEnv):
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

    def get_charging_station_by_id(self, **kwargs):
        return self._call_inner_tool('get_charging_station_by_id', kwargs)

    def search_charging_stations_by_coordinates(self, **kwargs):
        return self._call_inner_tool('search_charging_stations_by_coordinates', kwargs)

    def list_charging_stations_by_operator(self, **kwargs):
        return self._call_inner_tool('list_charging_stations_by_operator', kwargs)

    def get_charging_station_status(self, **kwargs):
        return self._call_inner_tool('get_charging_station_status', kwargs)

    def get_technical_specifications(self, **kwargs):
        return self._call_inner_tool('get_technical_specifications', kwargs)

    def get_operator_info(self, **kwargs):
        return self._call_inner_tool('get_operator_info', kwargs)

    def list_all_charging_stations(self, **kwargs):
        return self._call_inner_tool('list_all_charging_stations', kwargs)

    def validate_station_operator_reference(self, **kwargs):
        return self._call_inner_tool('validate_station_operator_reference', kwargs)

    def check_coordinates_validity(self, **kwargs):
        return self._call_inner_tool('check_coordinates_validity', kwargs)

    def add_charging_station(self, **kwargs):
        return self._call_inner_tool('add_charging_station', kwargs)

    def update_charging_station_details(self, **kwargs):
        return self._call_inner_tool('update_charging_station_details', kwargs)

    def delete_charging_station(self, **kwargs):
        return self._call_inner_tool('delete_charging_station', kwargs)

    def add_operator(self, **kwargs):
        return self._call_inner_tool('add_operator', kwargs)

    def update_operator_info(self, **kwargs):
        return self._call_inner_tool('update_operator_info', kwargs)

    def bulk_import_stations(self, **kwargs):
        return self._call_inner_tool('bulk_import_stations', kwargs)

    def update_charging_station_status(self, **kwargs):
        return self._call_inner_tool('update_charging_station_status', kwargs)

    def correct_station_coordinates(self, **kwargs):
        return self._call_inner_tool('correct_station_coordinates', kwargs)
