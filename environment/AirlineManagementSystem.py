# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
import uuid
from typing import Optional



class AirlineInfo(TypedDict):
    airline_id: str
    name: str
    country: str
    IATA_code: str
    ICAO_code: str
    fleet_size: int

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for managing airlines and their fleets.
        """

        # Airlines: {airline_id: AirlineInfo}
        self.airlines: Dict[str, AirlineInfo] = {}

        # Constraints:
        # - IATA_code must be unique among all airlines.
        # - ICAO_code must be unique among all airlines.
        # - fleet_size must be a non-negative integer.
        # - Updates to airlines should be referenced by a unique identifier (e.g., IATA_code or airline_id).
        # - An airline must have a name and a country before being added to the system.

    def get_airline_by_id(self, airline_id: str) -> dict:
        """
        Retrieve details of an airline using its internal unique airline_id.

        Args:
            airline_id (str): Internal unique identifier for the airline.

        Returns:
            dict: {
                "success": True,
                "data": AirlineInfo
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The airline with the provided airline_id must exist in the system.
        """
        airline = self.airlines.get(airline_id)
        if airline is None:
            return { "success": False, "error": "Airline with specified ID does not exist" }
        return { "success": True, "data": airline }

    def get_airline_by_IATA_code(self, IATA_code: str) -> dict:
        """
        Retrieve details of an airline with the specified IATA code.

        Args:
            IATA_code (str): The IATA code to search for (must be unique in the system).

        Returns:
            dict:
                - On success: { "success": True, "data": AirlineInfo }
                - On failure: { "success": False, "error": "No airline found with the specified IATA code" }

        Constraints:
            - IATA_code must be unique among all airlines.
        """
        for airline in self.airlines.values():
            if airline["IATA_code"] == IATA_code:
                return { "success": True, "data": airline }
        return { "success": False, "error": "No airline found with the specified IATA code" }

    def get_airline_by_ICAO_code(self, ICAO_code: str) -> dict:
        """
        Retrieve details of an airline with the specified ICAO code.

        Args:
            ICAO_code (str): The ICAO code for the airline to be retrieved.

        Returns:
            dict:
                - On success: {'success': True, 'data': AirlineInfo}
                - On failure: {'success': False, 'error': str}
        Constraints:
            - ICAO_code must be unique among all airlines.
        """
        for airline in self.airlines.values():
            if airline["ICAO_code"] == ICAO_code:
                return { "success": True, "data": airline }
        return { "success": False, "error": f"No airline with ICAO code '{ICAO_code}' found" }

    def list_all_airlines(self) -> dict:
        """
        Retrieve a list of all airlines currently stored in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[AirlineInfo]  # List of all airline infos, empty if none stored
            }
        """
        return {
            "success": True,
            "data": list(self.airlines.values())
        }

    def list_airlines_by_country(self, country: str) -> dict:
        """
        List all airlines operating in the specified country.

        Args:
            country (str): The name of the country to query airlines for.

        Returns:
            dict: {
                "success": True,
                "data": List[AirlineInfo],  # All airlines with a matching country (can be empty)
            }
            or
            {
                "success": False,
                "error": str  # If the input is invalid
            }

        Constraints:
            - Country must be a non-empty string.
        """
        if not isinstance(country, str) or not country.strip():
            return {"success": False, "error": "Invalid country parameter"}
    
        matched = [
            airline for airline in self.airlines.values()
            if airline.get("country", "").lower() == country.strip().lower()
        ]
        return {"success": True, "data": matched}

    def check_IATA_code_uniqueness(self, IATA_code: str) -> dict:
        """
        Check if the given IATA code is unique (not present in the system).

        Args:
            IATA_code (str): The IATA code to check for uniqueness.

        Returns:
            dict: {
                "success": True,
                "data": bool  # True if code is unique, False if code already exists in the system.
            }

        Constraints:
            - No error if input is empty or malformed; treated as a code to check.
            - Case-sensitive comparison.
        """
        is_unique = all(
            airline['IATA_code'] != IATA_code
            for airline in self.airlines.values()
        )
        return { "success": True, "data": is_unique }

    def check_ICAO_code_uniqueness(self, ICAO_code: str) -> dict:
        """
        Check if the given ICAO_code is unique (i.e., not already present in the system).

        Args:
            ICAO_code (str): The ICAO code to check.

        Returns:
            dict: {
                "success": True,
                "data": bool  # True if not present, False if already used
            }
            or {
                "success": False,
                "error": str        # Description of error (e.g. invalid input)
            }

        Constraints:
            - ICAO_code must be unique among all airlines.
        """
        if not isinstance(ICAO_code, str) or not ICAO_code:
            return { "success": False, "error": "Invalid ICAO_code input" }

        for airline in self.airlines.values():
            if airline["ICAO_code"] == ICAO_code:
                return { "success": True, "data": False }
        return { "success": True, "data": True }

    def validate_airline_required_fields(self, airline_data: dict) -> dict:
        """
        Checks if all required fields ('name', 'country') are present and non-empty in the provided airline data.

        Args:
            airline_data (dict): Dictionary with potential airline fields.

        Returns:
            dict: 
                - On success and all fields present: 
                    { "success": True, "data": { "valid": True } }
                - On success but fields missing/empty: 
                    { "success": True, "data": { "valid": False, "missing_fields": [<fields>] } }
                - On input error (not a dict):
                    { "success": False, "error": "Input must be a dictionary" }
    
        Constraints:
            - 'name' and 'country' fields must be present and non-empty.
        """
        if not isinstance(airline_data, dict):
            return { "success": False, "error": "Input must be a dictionary" }
    
        required_fields = ["name", "country"]
        missing_fields = [
            field for field in required_fields
            if field not in airline_data or not isinstance(airline_data[field], str) or not airline_data[field].strip()
        ]

        if missing_fields:
            return {
                "success": True,
                "data": {
                    "valid": False,
                    "missing_fields": missing_fields
                }
            }

        return {
            "success": True,
            "data": {
                "valid": True
            }
        }


    def add_airline(
        self,
        name: str,
        country: str,
        IATA_code: str,
        ICAO_code: str,
        fleet_size: Optional[int] = 0
    ) -> dict:
        """
        Add a new airline to the system after enforcing required field presence and code uniqueness.

        Args:
            name (str): Airline name (required, non-empty)
            country (str): Country (required, non-empty)
            IATA_code (str): IATA code (required, unique)
            ICAO_code (str): ICAO code (required, unique)
            fleet_size (int, optional): Fleet size (must be non-negative, default 0)

        Returns:
            dict:
                - On success: { "success": True, "message": "Airline added successfully", "airline_id": <id> }
                - On failure: { "success": False, "error": "reason" }

        Constraints:
            - IATA_code and ICAO_code must be unique.
            - fleet_size must be a non-negative integer.
            - name and country must be non-empty.
        """

        # Check required fields
        if not name or not country:
            return { "success": False, "error": "Airline 'name' and 'country' are required." }
        if not IATA_code or not ICAO_code:
            return { "success": False, "error": "Both IATA_code and ICAO_code are required." }
        # Validate fleet_size
        if fleet_size is None:
            fleet_size = 0
        if not isinstance(fleet_size, int) or fleet_size < 0:
            return { "success": False, "error": "Fleet size must be a non-negative integer." }

        # Check uniqueness of IATA_code and ICAO_code
        for existing in self.airlines.values():
            if existing["IATA_code"] == IATA_code:
                return { "success": False, "error": f"IATA_code '{IATA_code}' already exists." }
            if existing["ICAO_code"] == ICAO_code:
                return { "success": False, "error": f"ICAO_code '{ICAO_code}' already exists." }

        # Create airline_id
        airline_id = str(uuid.uuid4())

        # Add the new airline
        new_airline: AirlineInfo = {
            "airline_id": airline_id,
            "name": name,
            "country": country,
            "IATA_code": IATA_code,
            "ICAO_code": ICAO_code,
            "fleet_size": fleet_size
        }
        self.airlines[airline_id] = new_airline
    
        return {
            "success": True,
            "message": "Airline added successfully",
            "airline_id": airline_id
        }

    def update_airline_by_id(
        self,
        airline_id: str,
        name: str = None,
        country: str = None,
        IATA_code: str = None,
        ICAO_code: str = None,
        fleet_size: int = None
    ) -> dict:
        """
        Update airline details by airline_id.

        Args:
            airline_id (str): Unique ID of the airline to update.
            name (str, optional): New name of the airline.
            country (str, optional): New country.
            IATA_code (str, optional): New IATA code (must be unique).
            ICAO_code (str, optional): New ICAO code (must be unique).
            fleet_size (int, optional): New fleet size (must be non-negative).

        Returns:
            dict: {
              "success": True,
              "message": "Airline updated successfully."
            }
            or
            {
              "success": False,
              "error": "<reason>"
            }

        Constraints:
            - Airline must exist.
            - IATA_code and ICAO_code must remain unique if changed.
            - fleet_size, if changed, must be non-negative integer.
            - name and country, if provided, cannot be empty.
        """
        airline = self.airlines.get(airline_id)
        if not airline:
            return { "success": False, "error": "Airline with the specified 'airline_id' does not exist." }

        # IATA_code uniqueness
        if IATA_code is not None and IATA_code != airline["IATA_code"]:
            for a_id, a_info in self.airlines.items():
                if a_id != airline_id and a_info["IATA_code"] == IATA_code:
                    return { "success": False, "error": f"IATA_code '{IATA_code}' is already in use by another airline." }

        # ICAO_code uniqueness
        if ICAO_code is not None and ICAO_code != airline["ICAO_code"]:
            for a_id, a_info in self.airlines.items():
                if a_id != airline_id and a_info["ICAO_code"] == ICAO_code:
                    return { "success": False, "error": f"ICAO_code '{ICAO_code}' is already in use by another airline." }

        # Non-negative fleet_size
        if fleet_size is not None:
            if not isinstance(fleet_size, int) or fleet_size < 0:
                return { "success": False, "error": "fleet_size must be a non-negative integer." }

        # Non-empty checks
        if name is not None and not name.strip():
            return { "success": False, "error": "Airline name cannot be empty." }
        if country is not None and not country.strip():
            return { "success": False, "error": "Airline country cannot be empty." }

        # Perform updates
        if name is not None:
            airline["name"] = name
        if country is not None:
            airline["country"] = country
        if IATA_code is not None:
            airline["IATA_code"] = IATA_code
        if ICAO_code is not None:
            airline["ICAO_code"] = ICAO_code
        if fleet_size is not None:
            airline["fleet_size"] = fleet_size

        return { "success": True, "message": "Airline updated successfully." }

    def update_airline_by_IATA_code(
        self, 
        IATA_code: str, 
        name: str = None, 
        country: str = None, 
        new_IATA_code: str = None, 
        ICAO_code: str = None, 
        fleet_size: int = None
    ) -> dict:
        """
        Update the airline's details using its unique IATA code.

        Args:
            IATA_code (str): The IATA code of the airline to update (lookup key).
            name (str, optional): New name for the airline.
            country (str, optional): New country.
            new_IATA_code (str, optional): New IATA code (must remain unique).
            ICAO_code (str, optional): New ICAO code (must remain unique).
            fleet_size (int, optional): Updated fleet size (must be >= 0).

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "message": "Airline with IATA_code <IATA_code> updated successfully"
                }
                On failure: {
                    "success": False,
                    "error": "<reason>"
                }

        Constraints:
            - IATA_code and ICAO_code must remain unique among all airlines.
            - fleet_size must be a non-negative integer.
            - name and country must not be empty after update.
        """
        # Locate airline by IATA_code
        airline_id = None
        for aid, info in self.airlines.items():
            if info["IATA_code"] == IATA_code:
                airline_id = aid
                break
        if not airline_id:
            return {"success": False, "error": "Airline with specified IATA_code not found"}

        airline = self.airlines[airline_id]

        # Prepare new values (use current if not provided)
        updated = dict(airline)  # shallow copy
        if name is not None:
            updated["name"] = name
        if country is not None:
            updated["country"] = country
        if new_IATA_code is not None:
            if new_IATA_code != IATA_code:
                # Check uniqueness
                for a in self.airlines.values():
                    if a["IATA_code"] == new_IATA_code:
                        return {"success": False, "error": "IATA_code must be unique"}
                updated["IATA_code"] = new_IATA_code
        if ICAO_code is not None:
            if ICAO_code != airline["ICAO_code"]:
                for a in self.airlines.values():
                    if a["ICAO_code"] == ICAO_code:
                        return {"success": False, "error": "ICAO_code must be unique"}
                updated["ICAO_code"] = ICAO_code
        if fleet_size is not None:
            if not isinstance(fleet_size, int) or fleet_size < 0:
                return {"success": False, "error": "Fleet size must be a non-negative integer"}
            updated["fleet_size"] = fleet_size

        if not updated["name"] or not updated["country"]:
            return {"success": False, "error": "Airline must have a non-empty name and country"}

        # Apply changes
        self.airlines[airline_id] = updated
        msg = f"Airline with IATA_code {IATA_code} updated successfully"
        if new_IATA_code and new_IATA_code != IATA_code:
            msg = f"Airline IATA_code changed to {new_IATA_code} and updated successfully"
        return {"success": True, "message": msg}

    def update_airline_by_ICAO_code(self, ICAO_code: str, updates: dict) -> dict:
        """
        Update airline details by its ICAO code.

        Args:
            ICAO_code (str): The ICAO code of the airline to update.
            updates (dict): Dictionary of fields to update (keys: name, country, IATA_code, ICAO_code, fleet_size).

        Returns:
            dict: {
                "success": True,
                "message": "Airline updated successfully."
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - Must not update airline_id.
            - New IATA_code or ICAO_code (if changed) must be unique.
            - fleet_size must be non-negative integer.
            - Airline with given ICAO_code must exist.
        """
        # Find airline by ICAO_code
        airline_id = None
        for aid, info in self.airlines.items():
            if info["ICAO_code"] == ICAO_code:
                airline_id = aid
                break
        if airline_id is None:
            return {"success": False, "error": "No airline found with the given ICAO_code."}
    
        airline = self.airlines[airline_id]
        valid_fields = {"name", "country", "IATA_code", "ICAO_code", "fleet_size"}
        for field, value in updates.items():
            if field not in valid_fields:
                continue
            if field == "IATA_code":
                # Check uniqueness if IATA_code is being changed
                if value != airline["IATA_code"]:
                    for other in self.airlines.values():
                        if other["IATA_code"] == value:
                            return {"success": False, "error": "IATA_code already exists for another airline."}
                    airline["IATA_code"] = value
            elif field == "ICAO_code":
                # Check uniqueness if ICAO_code is being changed
                if value != airline["ICAO_code"]:
                    for other in self.airlines.values():
                        if other["ICAO_code"] == value:
                            return {"success": False, "error": "ICAO_code already exists for another airline."}
                    airline["ICAO_code"] = value
            elif field == "fleet_size":
                if not isinstance(value, int) or value < 0:
                    return {"success": False, "error": "fleet_size must be a non-negative integer."}
                airline["fleet_size"] = value
            else:
                airline[field] = value  # name, country
        self.airlines[airline_id] = airline
        return {"success": True, "message": "Airline updated successfully."}

    def delete_airline_by_id(self, airline_id: str) -> dict:
        """
        Remove an airline from the system using its airline_id.

        Args:
            airline_id (str): Internal unique identifier for the airline.

        Returns:
            dict:
                On success:
                {
                    "success": True,
                    "message": "Airline with id <airline_id> deleted successfully."
                }
                On failure:
                {
                    "success": False,
                    "error": "reason"
                }

        Constraints:
            - The airline_id must exist in the system.
        """
        if airline_id not in self.airlines:
            return { "success": False, "error": f"Airline with id {airline_id} does not exist." }

        del self.airlines[airline_id]
        return {
            "success": True,
            "message": f"Airline with id {airline_id} deleted successfully."
        }

    def delete_airline_by_IATA_code(self, IATA_code: str) -> dict:
        """
        Remove an airline record using its unique IATA_code.

        Args:
            IATA_code (str): The unique IATA code of the airline to be deleted.

        Returns:
            dict: {
                "success": True,
                "message": "Airline with IATA_code '<IATA_code>' deleted."
            }
            or
            {
                "success": False,
                "error": "Airline with IATA_code '<IATA_code>' not found."
            }

        Constraints:
            - IATA_code must exist among airlines.
            - All data related to that airline will be permanently removed from the system state.
        """
        # First, find the airline_id associated with the IATA code
        target_id = None
        for airline_id, info in self.airlines.items():
            if info["IATA_code"] == IATA_code:
                target_id = airline_id
                break

        if not target_id:
            return {
                "success": False,
                "error": f"Airline with IATA_code '{IATA_code}' not found."
            }

        del self.airlines[target_id]
        return {
            "success": True,
            "message": f"Airline with IATA_code '{IATA_code}' deleted."
        }

    def set_airline_fleet_size(self, airline_id: str, fleet_size: int) -> dict:
        """
        Update only the fleet_size of the given airline, enforcing non-negative integer validation.

        Args:
            airline_id (str): Unique identifier of the airline to update.
            fleet_size (int): The new fleet size (must be a non-negative integer).

        Returns:
            dict: {
                "success": True,
                "message": "Fleet size updated successfully"
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - airline_id must exist in the system.
            - fleet_size must be a non-negative integer.
        """
        # Validate airline existence
        if airline_id not in self.airlines:
            return {"success": False, "error": "Airline not found"}

        # Validate fleet_size type
        if not isinstance(fleet_size, int):
            return {"success": False, "error": "Fleet size must be an integer"}

        # Validate fleet_size value
        if fleet_size < 0:
            return {"success": False, "error": "Fleet size must be a non-negative integer"}

        self.airlines[airline_id]['fleet_size'] = fleet_size
        return {"success": True, "message": "Fleet size updated successfully"}


class AirlineManagementSystem(BaseEnv):
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

    def get_airline_by_id(self, **kwargs):
        return self._call_inner_tool('get_airline_by_id', kwargs)

    def get_airline_by_IATA_code(self, **kwargs):
        return self._call_inner_tool('get_airline_by_IATA_code', kwargs)

    def get_airline_by_ICAO_code(self, **kwargs):
        return self._call_inner_tool('get_airline_by_ICAO_code', kwargs)

    def list_all_airlines(self, **kwargs):
        return self._call_inner_tool('list_all_airlines', kwargs)

    def list_airlines_by_country(self, **kwargs):
        return self._call_inner_tool('list_airlines_by_country', kwargs)

    def check_IATA_code_uniqueness(self, **kwargs):
        return self._call_inner_tool('check_IATA_code_uniqueness', kwargs)

    def check_ICAO_code_uniqueness(self, **kwargs):
        return self._call_inner_tool('check_ICAO_code_uniqueness', kwargs)

    def validate_airline_required_fields(self, **kwargs):
        return self._call_inner_tool('validate_airline_required_fields', kwargs)

    def add_airline(self, **kwargs):
        return self._call_inner_tool('add_airline', kwargs)

    def update_airline_by_id(self, **kwargs):
        return self._call_inner_tool('update_airline_by_id', kwargs)

    def update_airline_by_IATA_code(self, **kwargs):
        return self._call_inner_tool('update_airline_by_IATA_code', kwargs)

    def update_airline_by_ICAO_code(self, **kwargs):
        return self._call_inner_tool('update_airline_by_ICAO_code', kwargs)

    def delete_airline_by_id(self, **kwargs):
        return self._call_inner_tool('delete_airline_by_id', kwargs)

    def delete_airline_by_IATA_code(self, **kwargs):
        return self._call_inner_tool('delete_airline_by_IATA_code', kwargs)

    def set_airline_fleet_size(self, **kwargs):
        return self._call_inner_tool('set_airline_fleet_size', kwargs)
