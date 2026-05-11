# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
from typing import Optional, Dict, Any, List
from datetime import datetime



class LocationInfo(TypedDict):
    latitude: float
    longitude: float
    elevation: float

class AirportInfo(TypedDict):
    airport_id: str
    name: str
    ICAO_code: str
    location: LocationInfo
    timezone: str

class WeatherReportInfo(TypedDict):
    report_id: str
    airport_id: str
    type: str  # "METAR" or "TAF"
    issue_time: str  # UTC timestamp (e.g. ISO 8601)
    validity_start_time: str  # UTC timestamp
    validity_end_time: str  # UTC timestamp
    raw_text: str
    parsed_data: dict  # schema to be refined as needed

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Aviation Weather Information System state.

        Constraints:
        - Each WeatherReport must be linked to a valid airport (airport_id must exist in airports).
        - All WeatherReport timestamps must be stored in standardized UTC format (e.g., ISO 8601).
        - Queries are supported by airport_id, type, and arbitrary (UTC) time ranges.
        - Historical (archived) WeatherReports are preserved for retrospective analysis.
        """

        # Airports: {airport_id: AirportInfo}
        self.airports: Dict[str, AirportInfo] = {}

        # WeatherReports: {report_id: WeatherReportInfo}
        self.weather_reports: Dict[str, WeatherReportInfo] = {}

    @staticmethod
    def _parse_iso_timestamp(timestamp: str) -> datetime:
        if not isinstance(timestamp, str):
            raise ValueError("timestamp must be a string")
        normalized = timestamp[:-1] + "+00:00" if timestamp.endswith("Z") else timestamp
        return datetime.fromisoformat(normalized)

    def get_airport_by_id(self, airport_id: str) -> dict:
        """
        Retrieve details of an airport using its airport_id.

        Args:
            airport_id (str): The unique identifier of the airport.

        Returns:
            dict:
                On success: { "success": True, "data": AirportInfo }
                On failure: { "success": False, "error": "Airport not found" }

        Constraints:
            - The airport_id must exist in the airport registry.
        """
        airport = self.airports.get(airport_id)
        if airport is None:
            return { "success": False, "error": "Airport not found" }
        return { "success": True, "data": airport }

    def list_airports(self) -> dict:
        """
        List all registered airports in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[AirportInfo],  # List of all airport records (may be empty)
            }
        """
        airports_list = list(self.airports.values())
        return {"success": True, "data": airports_list}

    def get_weather_reports_by_airport(self, airport_id: str) -> dict:
        """
        Retrieve all weather reports associated with the given airport.

        Args:
            airport_id (str): The ID of the airport to query.

        Returns:
            dict: 
                - On success: 
                    {
                        "success": True,
                        "data": [WeatherReportInfo, ...]  # List of all weather reports for the airport (may be empty)
                    }
                - On failure:
                    {
                        "success": False,
                        "error": str  # Error reason
                    }

        Constraints:
            - The provided airport_id must exist in the airports registry.
            - All matching weather reports (historical and current) are returned.
        """
        if airport_id not in self.airports:
            return {
                "success": False,
                "error": "Airport ID does not exist"
            }

        reports = [
            report for report in self.weather_reports.values()
            if report["airport_id"] == airport_id
        ]

        return {
            "success": True,
            "data": reports
        }

    def get_weather_reports_by_airport_and_type(self, airport_id: str, report_type: str) -> dict:
        """
        Retrieve all weather reports of a given type (METAR/TAF) for a specific airport.

        Args:
            airport_id (str): The airport identifier to search for.
            report_type (str): Must be either "METAR" or "TAF".

        Returns:
            dict: {
                "success": True,
                "data": List[WeatherReportInfo],  # May be empty if none exist
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (invalid airport, invalid report_type)
            }

        Constraints:
            - airport_id must exist in airports.
            - report_type must be "METAR" or "TAF" (case-insensitive).
        """
        valid_types = {"METAR", "TAF"}
        normalized_type = report_type.upper()
    
        if airport_id not in self.airports:
            return { "success": False, "error": "Airport does not exist" }
        if normalized_type not in valid_types:
            return { "success": False, "error": "Invalid report type" }
    
        matched_reports = [
            report for report in self.weather_reports.values()
            if report["airport_id"] == airport_id and report["type"].upper() == normalized_type
        ]
    
        return { "success": True, "data": matched_reports }

    def get_most_recent_weather_report_by_type(self, airport_id: str, report_type: str) -> dict:
        """
        Retrieve the most recent weather report of a specified type (e.g., 'METAR' or 'TAF') for a particular airport.

        Args:
            airport_id (str): The target airport's ID.
            report_type (str): The report type to filter by ("METAR" or "TAF").

        Returns:
            dict:
                On success:
                    {"success": True, "data": WeatherReportInfo}
                On failure:
                    {"success": False, "error": <error reason>}

        Constraints:
            - The airport_id must exist in the system.
            - The report_type should match exactly ("METAR" or "TAF").
            - Returns the most recent report by issue_time in UTC ISO 8601 format.
        """
        if airport_id not in self.airports:
            return { "success": False, "error": "Airport does not exist" }

        filtered = [
            report for report in self.weather_reports.values()
            if report["airport_id"] == airport_id and report["type"] == report_type
        ]
        if not filtered:
            return { "success": False, "error": "No matching weather report found" }

        # Find the report with the max issue_time (ISO 8601 lex order is correct if all in UTC)
        most_recent = max(filtered, key=lambda r: r["issue_time"])
        return { "success": True, "data": most_recent }

    def get_weather_reports_by_airport_type_and_time_range(
        self,
        airport_id: str,
        report_type: str,
        start_time: str,
        end_time: str
    ) -> dict:
        """
        Retrieve all weather reports of a specific type for a given airport within a specified UTC time range.

        Args:
            airport_id (str): The airport identifier.
            report_type (str): "METAR" or "TAF".
            start_time (str): Start of the UTC time range (inclusive), ISO 8601 string.
            end_time (str): End of the UTC time range (inclusive), ISO 8601 string.

        Returns:
            dict:
                - {"success": True, "data": List[WeatherReportInfo]}
                  If successful (list may be empty if no matching reports)
                - {"success": False, "error": str}
                  If the airport_id does not exist, report_type invalid, or time range invalid.

        Constraints:
            - The provided airport_id must exist in the system.
            - report_type must be "METAR" or "TAF".
            - start_time and end_time must be valid ISO 8601 UTC timestamps; start_time <= end_time.
            - Only WeatherReports with issue_time in [start_time, end_time] (inclusive) are returned.
        """
        # Check airport existence
        if airport_id not in self.airports:
            return {"success": False, "error": "Airport does not exist"}

        # Check report type validity
        if report_type not in ("METAR", "TAF"):
            return {"success": False, "error": "Invalid report type (must be 'METAR' or 'TAF')"}
        try:
            dt_start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            dt_end = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
        except Exception:
            return {"success": False, "error": "Invalid time range timestamps; must be valid ISO 8601 UTC timestamps"}
        if dt_start > dt_end:
            return {"success": False, "error": "Invalid time range: start_time is after end_time"}

        result = []
        for report in self.weather_reports.values():
            try:
                issue_dt = datetime.fromisoformat(report["issue_time"].replace("Z", "+00:00"))
            except Exception:
                continue
            if (
                report["airport_id"] == airport_id and
                report["type"] == report_type and
                dt_start <= issue_dt <= dt_end
            ):
                result.append(report)

        return {"success": True, "data": result}

    def get_weather_report_by_id(self, report_id: str) -> dict:
        """
        Retrieve detailed information on a weather report using its report_id.

        Args:
            report_id (str): Unique identifier of the weather report.

        Returns:
            dict:
                On success: {
                    "success": True,
                    "data": WeatherReportInfo
                }
                On failure: {
                    "success": False,
                    "error": "Weather report not found"
                }

        Constraints:
            - The report_id must exist in the weather_reports dictionary.
        """
        report = self.weather_reports.get(report_id)
        if report is None:
            return { "success": False, "error": "Weather report not found" }
        return { "success": True, "data": report }

    def get_parsed_data_from_report(self, report_id: str) -> dict:
        """
        Extract and return the structured parsed_data field from a WeatherReport.

        Args:
            report_id (str): The unique identifier of the weather report.

        Returns:
            dict:
                {
                    "success": True,
                    "data": dict,  # The parsed_data field of the WeatherReport
                }
                OR
                {
                    "success": False,
                    "error": str,  # "WeatherReport not found"
                }
        Constraints:
            - The report_id must exist in the system.
        """
        report = self.weather_reports.get(report_id)
        if not report:
            return {"success": False, "error": "WeatherReport not found"}
        return {"success": True, "data": report["parsed_data"]}


    def get_weather_report_trend_for_airport(
        self, 
        airport_id: str, 
        start_time: str, 
        end_time: str
    ) -> dict:
        """
        Analyze and return weather trend statistics for an airport based on a series of METAR 
        weather reports in a given UTC time range.

        Args:
            airport_id (str): The ID of the airport to analyze.
            start_time (str): Lower bound of UTC time range (inclusive), ISO 8601 string.
            end_time (str): Upper bound of UTC time range (inclusive), ISO 8601 string.

        Returns:
            dict: {
                "success": True,
                "data": trend_summaries   # dict[str,Any]: computed statistics (may be None/empty if no reports)
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Airport must exist.
            - start_time <= end_time (ISO 8601 UTC).
            - Only METAR reports from airport and within range are used.
        """
        # Validate airport exists
        if airport_id not in self.airports:
            return {"success": False, "error": "Airport does not exist"}

        # Parse start and end times
        try:
            dt_start = self._parse_iso_timestamp(start_time)
            dt_end = self._parse_iso_timestamp(end_time)
        except Exception:
            return {"success": False, "error": "Invalid start_time or end_time format; must be ISO 8601"}

        if dt_start > dt_end:
            return {"success": False, "error": "start_time must be before or equal to end_time"}

        # Filter relevant METAR reports
        metar_reports: List[Dict[str, Any]] = []
        for report in self.weather_reports.values():
            if (
                report['airport_id'] == airport_id 
                and report['type'] == 'METAR'
            ):
                try:
                    issue_dt = self._parse_iso_timestamp(report['issue_time'])
                except Exception:
                    continue  # skip malformed
                if dt_start <= issue_dt <= dt_end:
                    metar_reports.append(report)

        if not metar_reports:
            return {"success": True, "data": {"message": "No METAR reports found for this airport in the given range.", "trend": {}}}

        # Example trend statistics: average temperature, min/max wind speed, predominant weather condition
        # The actual field names below (e.g. temperature, wind_speed, condition) depend on system's 'parsed_data' structure.
        temps = []
        wind_speeds = []
        conditions = {}

        for report in metar_reports:
            pd = report.get("parsed_data", {})
            temp = pd.get("temperature")
            wind = pd.get("wind_speed")
            cond = pd.get("weather_condition")
            if isinstance(temp, (int, float)):
                temps.append(temp)
            if isinstance(wind, (int, float)):
                wind_speeds.append(wind)
            if cond:
                conditions[cond] = conditions.get(cond, 0) + 1

        trend = {}
        if temps:
            trend["avg_temperature"] = sum(temps) / len(temps)
            trend["min_temperature"] = min(temps)
            trend["max_temperature"] = max(temps)
        if wind_speeds:
            trend["avg_wind_speed"] = sum(wind_speeds) / len(wind_speeds)
            trend["min_wind_speed"] = min(wind_speeds)
            trend["max_wind_speed"] = max(wind_speeds)
        if conditions:
            predominant = max(conditions.items(), key=lambda x: x[1])[0]
            trend["predominant_weather_condition"] = predominant

        return {"success": True, "data": {"message": "Trend computed", "trend": trend}}

    def add_airport(
        self,
        airport_id: str,
        name: str,
        ICAO_code: str,
        location: dict,
        timezone: str
    ) -> dict:
        """
        Register a new airport in the system.

        Args:
            airport_id (str): Unique identifier for the airport.
            name (str): Airport name.
            ICAO_code (str): ICAO code.
            location (dict): Dict with latitude (float), longitude (float), elevation (float).
            timezone (str): Timezone string.

        Returns:
            dict:
                - On success: { "success": True, "message": "Airport added successfully" }
                - On error (duplicate): { "success": False, "error": "Airport with this airport_id already exists" }
                - On malformed location: { "success": False, "error": "Invalid location data" }

        Constraints:
            - airport_id must be unique in the system.
        """
        if airport_id in self.airports:
            return { "success": False, "error": "Airport with this airport_id already exists" }

        # Minimal location validation (robustness, not strictly in spec):
        required_keys = {"latitude", "longitude", "elevation"}
        if not isinstance(location, dict) or not required_keys.issubset(location.keys()):
            return { "success": False, "error": "Invalid location data" }
        try:
            latitude = float(location["latitude"])
            longitude = float(location["longitude"])
            elevation = float(location["elevation"])
        except (ValueError, TypeError):
            return { "success": False, "error": "Invalid location data" }

        airport_info = {
            "airport_id": airport_id,
            "name": name,
            "ICAO_code": ICAO_code,
            "location": {
                "latitude": latitude,
                "longitude": longitude,
                "elevation": elevation
            },
            "timezone": timezone
        }
        self.airports[airport_id] = airport_info
        return { "success": True, "message": "Airport added successfully" }

    def add_weather_report(
        self,
        report_id: str,
        airport_id: str,
        type: str,
        issue_time: str,
        validity_start_time: str,
        validity_end_time: str,
        raw_text: str,
        parsed_data: dict
    ) -> dict:
        """
        Add a new WeatherReport to the system.

        Args:
            report_id (str): Unique report identifier (must not already exist).
            airport_id (str): Associated airport (must exist).
            type (str): "METAR" or "TAF".
            issue_time (str): UTC ISO 8601 timestamp, e.g. "2024-05-29T14:00:00Z".
            validity_start_time (str): UTC ISO 8601 timestamp.
            validity_end_time (str): UTC ISO 8601 timestamp.
            raw_text (str): The raw weather message.
            parsed_data (dict): Dictionary with parsed weather fields.

        Returns:
            dict: {
                "success": True,
                "message": "WeatherReport added successfully"
            }
            or {
                "success": False,
                "error": str  # description of error
            }

        Constraints:
            - airport_id must exist in self.airports.
            - All timestamps must be UTC format.
            - report_id must be unique.
        """
        # Check for unique report_id
        if report_id in self.weather_reports:
            return { "success": False, "error": "report_id already exists" }

        # Check if airport exists
        if airport_id not in self.airports:
            return { "success": False, "error": "airport_id does not exist" }
        if type not in ("METAR", "TAF"):
            return { "success": False, "error": "type must be 'METAR' or 'TAF'" }

        # Helper for UTC check (ISO 8601 UTC usually ends with 'Z' or '+00:00')
        def is_utc(ts: str) -> bool:
            return ts.endswith('Z') or ts.endswith('+00:00')

        for ts, label in [
            (issue_time, "issue_time"),
            (validity_start_time, "validity_start_time"),
            (validity_end_time, "validity_end_time"),
        ]:
            if not is_utc(ts):
                return {
                    "success": False,
                    "error": f"{label} must be in standardized UTC format (ISO 8601)"
                }

        # Store the new report
        self.weather_reports[report_id] = {
            "report_id": report_id,
            "airport_id": airport_id,
            "type": type,
            "issue_time": issue_time,
            "validity_start_time": validity_start_time,
            "validity_end_time": validity_end_time,
            "raw_text": raw_text,
            "parsed_data": parsed_data,
        }
        return { "success": True, "message": "WeatherReport added successfully" }

    def update_weather_report(
        self, 
        report_id: str, 
        airport_id: str = None, 
        type: str = None, 
        issue_time: str = None,
        validity_start_time: str = None,
        validity_end_time: str = None,
        raw_text: str = None,
        parsed_data: dict = None
    ) -> dict:
        """
        Modify the contents of an existing weather report.
    
        Args:
            report_id (str): The unique identifier of the weather report to update.
            airport_id (str, optional): New airport ID (must exist in system).
            type (str, optional): "METAR" or "TAF".
            issue_time (str, optional): New UTC issue timestamp (ISO8601).
            validity_start_time (str, optional): New UTC start timestamp.
            validity_end_time (str, optional): New UTC end timestamp.
            raw_text (str, optional): New raw weather data string.
            parsed_data (dict, optional): New parsed weather data.
    
        Returns:
            dict: 
                { "success": True, "message": "Weather report updated successfully." }
                Or
                { "success": False, "error": str }
    
        Constraints:
            - report_id must exist in the system.
            - If airport_id is updated, it must refer to a valid airport.
            - Only updates provided fields; unknown fields are ignored.
        """
        wr = self.weather_reports.get(report_id)
        if not wr:
            return { "success": False, "error": "Weather report not found." }

        # If updating airport_id, validate existence
        if airport_id is not None:
            if airport_id not in self.airports:
                return { "success": False, "error": "Provided airport_id does not exist." }
            wr["airport_id"] = airport_id

        if type is not None:
            if type not in ["METAR", "TAF"]:
                return { "success": False, "error": "Weather report type must be 'METAR' or 'TAF'." }
            wr["type"] = type

        if issue_time is not None:
            wr["issue_time"] = issue_time

        if validity_start_time is not None:
            wr["validity_start_time"] = validity_start_time

        if validity_end_time is not None:
            wr["validity_end_time"] = validity_end_time

        if raw_text is not None:
            wr["raw_text"] = raw_text

        if parsed_data is not None:
            wr["parsed_data"] = parsed_data

        return { "success": True, "message": "Weather report updated successfully." }

    def delete_weather_report(self, report_id: str) -> dict:
        """
        Remove a weather report from the system, provided that deletion does not violate
        archival and regulatory compliance. Reports that are already archived, or if
        compliance requires archiving instead, cannot be deleted.

        Args:
            report_id (str): The identifier for the weather report to remove.

        Returns:
            dict: Success or error message.
                - On success: {
                      "success": True,
                      "message": "<report_id> deleted"
                  }
                - On failure: {
                      "success": False,
                      "error": <reason>
                  }
        Constraints:
            - If historical compliance requires preservation, refuse deletion and recommend archiving instead.
            - If the report does not exist, fail.
        """
        # Check for existence
        if report_id not in self.weather_reports:
            return {"success": False, "error": "Weather report not found"}

        # Check for potential archival/compliance logic
        report_info = self.weather_reports[report_id]
        if "archived" in report_info and report_info["archived"]:
            return {"success": False, "error": "Report is already archived and cannot be deleted due to historical compliance."}

        if report_info.get("compliance_preservation_required"):
            return {
                "success": False,
                "error": "Deletion blocked by compliance preservation requirements; archive the report instead."
            }

        # Simple compliance check: if policy says preserve for history, prevent deletion.
        # For this environment, we assume deletion is only permitted if NOT already archived.
        # (If archiving system exists, recommend that instead.)

        # Delete the weather report
        del self.weather_reports[report_id]
        return {"success": True, "message": f"Weather report '{report_id}' deleted"}

    def delete_airport(self, airport_id: str) -> dict:
        """
        Remove an airport from the system by its airport_id.
    
        Args:
            airport_id (str): The ID of the airport to remove.

        Returns:
            dict:
                - On success: {"success": True, "message": "Airport <ID> deleted."}
                - On failure: {"success": False, "error": <reason>}
    
        Constraints:
            - Blocks deletion if any WeatherReport is linked to this airport.
            - Ensures WeatherReport referential integrity and archival value.
        """
        if airport_id not in self.airports:
            return { "success": False, "error": f"Airport '{airport_id}' does not exist." }

        reports_exist = any(
            report_info["airport_id"] == airport_id and not report_info.get("archived", False)
            for report_info in self.weather_reports.values()
        )
        if reports_exist:
            return {
                "success": False,
                "error": (
                    f"Cannot delete airport '{airport_id}': "
                    "Weather reports linked to this airport exist. "
                    "Please delete or archive associated reports first."
                )
            }
    
        del self.airports[airport_id]
        return { "success": True, "message": f"Airport '{airport_id}' deleted." }

    def archive_weather_report(self, report_id: str) -> dict:
        """
        Mark a weather report as archived (logical deletion for audit compliance).
    
        Args:
            report_id (str): Identifier of the weather report to archive.
        
        Returns:
            dict: 
                - On success: {"success": True, "message": "Weather report archived"}
                - If already archived: {"success": True, "message": "Weather report was already archived"}
                - On error (not found): {"success": False, "error": "Weather report does not exist"}
    
        Constraints:
            - Physical deletion does not occur; only an 'archived' flag is set to True on the report.
            - Rest of report data remains unchanged.
            - Operation is idempotent.
        """
        if report_id not in self.weather_reports:
            return {"success": False, "error": "Weather report does not exist"}

        report = self.weather_reports[report_id]
        # Add archived key if not present
        if "archived" not in report:
            report["archived"] = False

        if report["archived"]:
            return {"success": True, "message": "Weather report was already archived"}

        report["archived"] = True
        return {"success": True, "message": "Weather report archived"}


class AviationWeatherInformationSystem(BaseEnv):
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

    def get_airport_by_id(self, **kwargs):
        return self._call_inner_tool('get_airport_by_id', kwargs)

    def list_airports(self, **kwargs):
        return self._call_inner_tool('list_airports', kwargs)

    def get_weather_reports_by_airport(self, **kwargs):
        return self._call_inner_tool('get_weather_reports_by_airport', kwargs)

    def get_weather_reports_by_airport_and_type(self, **kwargs):
        return self._call_inner_tool('get_weather_reports_by_airport_and_type', kwargs)

    def get_most_recent_weather_report_by_type(self, **kwargs):
        return self._call_inner_tool('get_most_recent_weather_report_by_type', kwargs)

    def get_weather_reports_by_airport_type_and_time_range(self, **kwargs):
        return self._call_inner_tool('get_weather_reports_by_airport_type_and_time_range', kwargs)

    def get_weather_report_by_id(self, **kwargs):
        return self._call_inner_tool('get_weather_report_by_id', kwargs)

    def get_parsed_data_from_report(self, **kwargs):
        return self._call_inner_tool('get_parsed_data_from_report', kwargs)

    def get_weather_report_trend_for_airport(self, **kwargs):
        return self._call_inner_tool('get_weather_report_trend_for_airport', kwargs)

    def add_airport(self, **kwargs):
        return self._call_inner_tool('add_airport', kwargs)

    def add_weather_report(self, **kwargs):
        return self._call_inner_tool('add_weather_report', kwargs)

    def update_weather_report(self, **kwargs):
        return self._call_inner_tool('update_weather_report', kwargs)

    def delete_weather_report(self, **kwargs):
        return self._call_inner_tool('delete_weather_report', kwargs)

    def delete_airport(self, **kwargs):
        return self._call_inner_tool('delete_airport', kwargs)

    def archive_weather_report(self, **kwargs):
        return self._call_inner_tool('archive_weather_report', kwargs)
