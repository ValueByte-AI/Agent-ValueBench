# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
import json
from typing import Dict, Any



class VehicleInfo(TypedDict):
    vin: str
    make: str
    model: str
    year: int  # fixed typo from 'yea'

class VehicleHistoryReportInfo(TypedDict):
    report_id: str
    vin: str
    status: str
    generated_at: str
    report_data: str

class AccidentRecordInfo(TypedDict):
    record_id: str
    vin: str
    date: str
    description: str

class OwnershipRecordInfo(TypedDict):
    record_id: str
    vin: str
    owner_id: str
    date_from: str
    date_to: str

class ServiceRecordInfo(TypedDict):
    record_id: str
    vin: str
    service_type: str
    service_date: str
    detail: str

class UserRequestInfo(TypedDict):
    request_id: str
    user_id: str
    vin: str
    report_id: str
    request_time: str
    status: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        State for vehicle history reporting system.
        """

        # Vehicles: {vin: VehicleInfo}
        self.vehicles: Dict[str, VehicleInfo] = {}

        # VehicleHistoryReports: {report_id: VehicleHistoryReportInfo}
        self.history_reports: Dict[str, VehicleHistoryReportInfo] = {}

        # AccidentRecords: {record_id: AccidentRecordInfo}
        self.accident_records: Dict[str, AccidentRecordInfo] = {}

        # OwnershipRecords: {record_id: OwnershipRecordInfo}
        self.ownership_records: Dict[str, OwnershipRecordInfo] = {}

        # ServiceRecords: {record_id: ServiceRecordInfo}
        self.service_records: Dict[str, ServiceRecordInfo] = {}

        # UserRequests: {request_id: UserRequestInfo}
        self.user_requests: Dict[str, UserRequestInfo] = {}

        # Constraint notes:
        # - Each VIN can only have one active vehicle history report at a time.
        # - A vehicle history report can only be generated if the vehicle (VIN) exists in the system.
        # - Reports must include all accident, ownership, and service records for the associated VIN.
        # - User requests for reports must reference existing VINs.

    @staticmethod
    def _parse_datetime(value: Any):
        if not isinstance(value, str):
            return None
        text = value.strip()
        if not text:
            return None
        candidates = [text]
        if text.endswith("Z"):
            candidates.append(text[:-1] + "+00:00")
        elif "T" in text and "+" not in text and "-" in text[10:]:
            candidates.append(text + "+00:00")
        elif "T" in text:
            candidates.append(text + "+00:00")
        if len(text) == 10:
            candidates.append(text + "T00:00:00+00:00")
        if " " in text and "+" not in text:
            candidates.append(text.replace(" ", "T") + "+00:00")
        for candidate in candidates:
            try:
                parsed = datetime.fromisoformat(candidate)
                if parsed.tzinfo is not None:
                    parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
                return parsed
            except Exception:
                continue
        return None

    @staticmethod
    def _format_datetime(value: datetime) -> str:
        return value.strftime("%Y-%m-%dT%H:%M:%SZ")

    @staticmethod
    def _sanitize_vin_for_id(vin: str) -> str:
        cleaned = "".join(ch for ch in str(vin) if ch.isalnum()).upper()
        return cleaned or "VIN"

    def _vehicle_exists_in_state(self, vin: str) -> bool:
        if vin in self.vehicles:
            return True
        return any(vehicle.get("vin") == vin for vehicle in self.vehicles.values())

    def _get_vehicle_record(self, vin: str):
        vehicle_info = self.vehicles.get(vin)
        if vehicle_info:
            return vehicle_info
        for vehicle_info in self.vehicles.values():
            if vehicle_info.get("vin") == vin:
                return vehicle_info
        return None

    @staticmethod
    def _current_report_statuses():
        return {"active", "in-progress", "completed", "generating", "exists"}

    def _current_reports_for_vin(self, vin: str):
        reports = [
            report for report in self.history_reports.values()
            if report.get("vin") == vin and report.get("status") in self._current_report_statuses()
        ]
        reports.sort(
            key=lambda report: (
                self._parse_datetime(report.get("generated_at")) or datetime.min,
                report.get("report_id", ""),
            )
        )
        return reports

    def _next_generated_at(self, vin: str) -> str:
        candidates = []
        for report in self.history_reports.values():
            if report.get("vin") == vin:
                parsed = self._parse_datetime(report.get("generated_at"))
                if parsed is not None:
                    candidates.append(parsed)
        for request in self.user_requests.values():
            if request.get("vin") == vin:
                parsed = self._parse_datetime(request.get("request_time"))
                if parsed is not None:
                    candidates.append(parsed)
        for record in self.accident_records.values():
            if record.get("vin") == vin:
                parsed = self._parse_datetime(record.get("date"))
                if parsed is not None:
                    candidates.append(parsed)
        for record in self.ownership_records.values():
            if record.get("vin") == vin:
                for field in ("date_from", "date_to"):
                    parsed = self._parse_datetime(record.get(field))
                    if parsed is not None:
                        candidates.append(parsed)
        for record in self.service_records.values():
            if record.get("vin") == vin:
                parsed = self._parse_datetime(record.get("service_date"))
                if parsed is not None:
                    candidates.append(parsed)
        if not candidates:
            return "1970-01-01T00:00:01Z"
        return self._format_datetime(max(candidates) + timedelta(seconds=1))

    def _next_report_id(self, vin: str) -> str:
        configured = getattr(self, "next_report_ids", None)
        if isinstance(configured, dict):
            preset = configured.get(vin)
            if isinstance(preset, list) and preset:
                report_id = str(preset.pop(0))
                configured[vin] = preset
                return report_id
            if isinstance(preset, str) and preset:
                configured[vin] = []
                return preset
        safe_vin = self._sanitize_vin_for_id(vin)
        prefix = f"REP-{safe_vin}-"
        max_idx = 0
        for report in self.history_reports.values():
            report_id = str(report.get("report_id", ""))
            if report_id.startswith(prefix):
                suffix = report_id[len(prefix):]
                if suffix.isdigit():
                    max_idx = max(max_idx, int(suffix))
        return f"{prefix}{max_idx + 1:03d}"

    def _build_report_payload(self, vin: str):
        accidents = [
            rec for rec in self.accident_records.values()
            if rec["vin"] == vin
        ]
        ownerships = [
            rec for rec in self.ownership_records.values()
            if rec["vin"] == vin
        ]
        services = [
            rec for rec in self.service_records.values()
            if rec["vin"] == vin
        ]
        report_data = {
            "accident_records": accidents,
            "ownership_records": ownerships,
            "service_records": services,
        }
        return report_data, json.dumps(report_data, sort_keys=True)

    def get_vehicle_by_vin(self, vin: str) -> dict:
        """
        Retrieve the information (make, model, year) for a vehicle by its VIN.

        Args:
            vin (str): The Vehicle Identification Number to query.

        Returns:
            dict:
                - success (bool): True if found, otherwise False.
                - data (VehicleInfo): The vehicle's identifying info, if found.
                - error (str): Error message if VIN does not exist.

        Constraints:
            - The specified VIN must exist in the system.
        """
        vehicle_info = self._get_vehicle_record(vin)
        if not vehicle_info:
            return { "success": False, "error": "Vehicle with specified VIN does not exist" }
        return { "success": True, "data": vehicle_info }

    def vehicle_exists(self, vin: str) -> dict:
        """
        Check if a given VIN exists in the vehicle system.

        Args:
            vin (str): The Vehicle Identification Number to check.

        Returns:
            dict: {
                "success": True,
                "data": { "exists": bool }
            }
                - exists: True if VIN exists in self.vehicles, False otherwise.

        Constraints:
            - VIN must be a non-empty string.
            - If VIN is empty or None, treat as not existing.
        """
        if not vin or not isinstance(vin, str):
            return {"success": True, "data": {"exists": False}}

        exists = self._vehicle_exists_in_state(vin)
        return {"success": True, "data": {"exists": exists}}

    def get_history_report_by_vin(self, vin: str) -> dict:
        """
        Retrieve all vehicle history report details for a specified VIN.

        Args:
            vin (str): Vehicle Identification Number.

        Returns:
            dict:
              - On success: {
                    "success": True,
                    "data": List[VehicleHistoryReportInfo]  # Possibly empty if no report exists for this VIN.
                }
              - On error: {
                    "success": False,
                    "error": "VIN does not exist"
                }

        Constraints:
            - The VIN must exist in the system.
        """
        if not self._vehicle_exists_in_state(vin):
            return { "success": False, "error": "VIN does not exist" }

        reports = [
            report for report in self.history_reports.values()
            if report["vin"] == vin
        ]

        return { "success": True, "data": reports }

    def get_active_history_report_by_vin(self, vin: str) -> dict:
        """
        Retrieve the single currently active vehicle history report for a VIN.

        Args:
            vin (str): The vehicle's unique identification number.

        Returns:
            dict:
                {
                    "success": True,
                    "data": VehicleHistoryReportInfo or None  # Active report info if found, else None
                }
                or
                {
                    "success": False,
                    "error": str  # Reason for failure (e.g., VIN does not exist)
                }

        Constraints:
            - The VIN must exist in the vehicles database.
            - At most one report can be active for a given VIN.
            - "Active" status is assumed to be "active", but could be adjusted if domain uses e.g. 'in-progress', etc.
        """
        # Ensure VIN exists
        if not self._vehicle_exists_in_state(vin):
            return {"success": False, "error": "VIN does not exist"}

        active_reports = self._current_reports_for_vin(vin)
        report_data = active_reports[-1] if active_reports else None

        return {"success": True, "data": report_data}

    def get_history_report_by_id(self, report_id: str) -> dict:
        """
        Retrieve the details of a vehicle history report using its report_id.

        Args:
            report_id (str): The unique identifier for the history report.

        Returns:
            dict: 
                - If found: { "success": True, "data": VehicleHistoryReportInfo }
                - If not found: { "success": False, "error": "Report not found" }

        Constraints:
            - The report_id must exist in the system.
        """
        report = self.history_reports.get(report_id)
        if report is None:
            return { "success": False, "error": "Report not found" }
        return { "success": True, "data": report }

    def list_reports_by_vin(self, vin: str) -> dict:
        """
        List all vehicle history reports that have ever existed for a specified VIN, regardless of report status.

        Args:
            vin (str): The vehicle identification number.

        Returns:
            dict: {
                "success": True,
                "data": List[VehicleHistoryReportInfo],
            }
            or
            {
                "success": False,
                "error": str  # If VIN does not exist
            }

        Constraints:
            - The VIN must exist in the system.
        """
        if not self._vehicle_exists_in_state(vin):
            return { "success": False, "error": "VIN does not exist in the system" }

        reports = [
            report for report in self.history_reports.values()
            if report["vin"] == vin
        ]

        return { "success": True, "data": reports }

    def get_accident_records_by_vin(self, vin: str) -> dict:
        """
        List all accident records associated with a given VIN.

        Args:
            vin (str): The Vehicle Identification Number.

        Returns:
            dict: {
                "success": True,
                "data": List[AccidentRecordInfo]  # List of accident records for the VIN (empty if none)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., VIN does not exist)
            }

        Constraints:
            - The VIN must exist in the system's vehicles database.
        """
        if not self._vehicle_exists_in_state(vin):
            return {"success": False, "error": "VIN does not exist"}

        accident_list = [
            record for record in self.accident_records.values()
            if record["vin"] == vin
        ]
        return {"success": True, "data": accident_list}

    def get_ownership_records_by_vin(self, vin: str) -> dict:
        """
        List all ownership history records for a given VIN.
    
        Args:
            vin (str): The vehicle identification number for which to retrieve ownership records.

        Returns:
            dict: 
              - On success: { "success": True, "data": List[OwnershipRecordInfo] }
              - On error (VIN does not exist): { "success": False, "error": "VIN does not exist" }

        Constraints:
            - VIN must exist in the vehicles registry.
            - Returns all ownership records for the specified VIN (possibly empty).
        """
        if not self._vehicle_exists_in_state(vin):
            return { "success": False, "error": "VIN does not exist" }
    
        records = [
            record for record in self.ownership_records.values()
            if record["vin"] == vin
        ]
        return { "success": True, "data": records }

    def get_service_records_by_vin(self, vin: str) -> dict:
        """
        List all service and maintenance records for a given VIN.

        Args:
            vin (str): The Vehicle Identification Number.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[ServiceRecordInfo]  # All service records for this VIN (can be empty)
                    }
                On failure (VIN does not exist):
                    {
                        "success": False,
                        "error": "VIN does not exist"
                    }

        Constraints:
            - VIN must exist in the system.
        """
        if not self._vehicle_exists_in_state(vin):
            return {"success": False, "error": "VIN does not exist"}
    
        records = [
            rec for rec in self.service_records.values()
            if rec["vin"] == vin
        ]

        return {"success": True, "data": records}

    def get_user_request_by_id(self, request_id: str) -> dict:
        """
        Retrieve the full details of a user request given its request_id.

        Args:
            request_id (str): The unique identifier for the user request.

        Returns:
            dict: 
                On success: { "success": True, "data": UserRequestInfo }
                On failure: { "success": False, "error": "User request not found" }
        Constraints:
            - The request_id must exist in the system.
        """
        user_request = self.user_requests.get(request_id)
        if user_request is None:
            return { "success": False, "error": "User request not found" }
        return { "success": True, "data": user_request }

    def get_user_requests_by_vin(self, vin: str) -> dict:
        """
        List all user requests (current and past) for a given VIN.

        Args:
            vin (str): The vehicle identification number to list requests for.

        Returns:
            dict:
                On success:
                {
                    "success": True,
                    "data": List[UserRequestInfo]  # All requests associated with the VIN, possibly empty
                }
                On failure:
                {
                    "success": False,
                    "error": str  # Reason (e.g., VIN does not exist)
                }
        Constraints:
            - The VIN must exist in the vehicle list.
        """
        if not self._vehicle_exists_in_state(vin):
            return { "success": False, "error": "VIN does not exist" }

        requests = [
            req for req in self.user_requests.values()
            if req["vin"] == vin
        ]

        return { "success": True, "data": requests }

    def get_latest_user_request_for_vin(self, vin: str) -> dict:
        """
        Retrieve the most recent user report request for the specified VIN.

        Args:
            vin (str): The Vehicle Identification Number to find the latest user request for.

        Returns:
            dict: {
                "success": True,
                "data": UserRequestInfo,  # The latest user request info for this VIN
            }
            or
            {
                "success": False,
                "error": str  # Error message if VIN does not exist or no requests found
            }

        Constraints:
            - The provided VIN must exist in the system (self.vehicles).
        """
        if not self._vehicle_exists_in_state(vin):
            return {"success": False, "error": "VIN does not exist in the system"}
    
        # Filter all user requests for this VIN
        vin_requests = [
            req_info for req_info in self.user_requests.values()
            if req_info['vin'] == vin
        ]
        if not vin_requests:
            return {"success": False, "error": "No user requests found for this VIN"}

        # Find the latest by request_time (assumes string comparison is sufficient)
        latest_request = max(vin_requests, key=lambda req: req['request_time'])
        return {"success": True, "data": latest_request}

    def get_report_status(self, report_id: str) -> dict:
        """
        Retrieve the status (e.g., exists, in-progress, completed) of a specific vehicle history report.

        Args:
            report_id (str): The unique identifier for the vehicle history report.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": { "status": str }
                    }
                On failure (report not found):
                    {
                        "success": False,
                        "error": "Report not found"
                    }
        """
        report = self.history_reports.get(report_id)
        if not report:
            return { "success": False, "error": "Report not found" }
        return { "success": True, "data": { "status": report["status"] } }

    def validate_report_includes_all_records(self, report_id: str) -> dict:
        """
        Check if a given vehicle history report contains all accident, ownership, and service records
        for the associated VIN.

        Args:
            report_id (str): The report's unique identifier.

        Returns:
            dict: {
                "success": True,
                "data": True/False  # True if all records are included, False otherwise
            }
            or
            {
                "success": False,
                "error": str  # Explanation, e.g., report not found
            }

        Constraints:
            - The report must exist in the system.
            - All accident, ownership, and service records for the VIN must be represented in the report_data
              (by containing their record_id as a substring).
        """
        report = self.history_reports.get(report_id)
        if not report:
            return {"success": False, "error": "Report not found"}

        vin = report["vin"]
        report_data = report.get("report_data", "")

        # Collect all relevant record_ids for this VIN
        accident_ids = [
            rec["record_id"]
            for rec in self.accident_records.values()
            if rec["vin"] == vin
        ]
        ownership_ids = [
            rec["record_id"]
            for rec in self.ownership_records.values()
            if rec["vin"] == vin
        ]
        service_ids = [
            rec["record_id"]
            for rec in self.service_records.values()
            if rec["vin"] == vin
        ]
        all_needed_ids = set(accident_ids + ownership_ids + service_ids)

        # Validate presence of each id in report_data
        all_present = all(record_id in report_data for record_id in all_needed_ids)
    
        return {"success": True, "data": all_present}


    def create_vehicle_history_report(self, vin: str) -> dict:
        """
        Generate a new vehicle history report for a VIN, if the vehicle exists
        and no active report is currently present. 
        The report will include all accident, ownership, and service records for the given VIN.

        Args:
            vin (str): The vehicle identification number.

        Returns:
            dict: {
                "success": True,
                "message": "Vehicle history report generated",
                "report_id": str,   # The new report ID
            }
            or
            {
                "success": False,
                "error": str
            }
    
        Constraints:
            - The given VIN must exist in the system.
            - Only one active report per VIN. ("active" means status NOT in {"archived", "deleted"})
            - The new report must include all accident, ownership, and service records for the VIN.
        """

        # 1. VIN must exist
        if not self._vehicle_exists_in_state(vin):
            return { "success": False, "error": "VIN does not exist" }

        # 2. Cannot generate if there's an active report for this VIN
        for report in self.history_reports.values():
            if report["vin"] == vin and report["status"] in self._current_report_statuses():
                return { "success": False, "error": "An active report already exists for this VIN" }

        report_data, report_data_str = self._build_report_payload(vin)
        report_id = self._next_report_id(vin)
        generated_at = self._next_generated_at(vin)

        # 6. Create record and store
        new_report = {
            "report_id": report_id,
            "vin": vin,
            "status": "in-progress",
            "generated_at": generated_at,
            "report_data": report_data_str,
        }
        self.history_reports[report_id] = new_report

        return {
            "success": True,
            "message": "Vehicle history report generated",
            "report_id": report_id,
        }

    def update_history_report_status(self, report_id: str, new_status: str) -> dict:
        """
        Change the status of a vehicle history report.

        Args:
            report_id (str): The unique identifier for the report to update.
            new_status (str): The new status to assign (e.g., 'in-progress', 'completed').

        Returns:
            dict: {
                'success': True,
                'message': 'Report status updated successfully.'
            }
            or
            {
                'success': False,
                'error': 'Report not found.'
            }

        Constraints:
            - Operation fails if report_id does not exist.
            - No check is made on status value validity (any string allowed).
        """
        if report_id not in self.history_reports:
            return {"success": False, "error": "Report not found."}

        self.history_reports[report_id]["status"] = new_status
        return {"success": True, "message": "Report status updated successfully."}


    def regenerate_history_report(self, vin: str) -> dict:
        """
        Invalidate a previous vehicle history report (if any) for the specified VIN, and create a new one.

        Args:
            vin (str): Vehicle Identification Number.

        Returns:
            dict: {
              "success": True,
              "message": str,
              "report_id": str   # Newly generated report id
            }
            or
            {
              "success": False,
              "error": str
            }

        Constraints:
            - VIN must exist in the system.
            - Only one active vehicle history report per VIN; previous one(s) are invalidated.
            - New report must include all accident, ownership, and service records for the VIN.
        """
        # 1. Check if vehicle exists
        if not self._vehicle_exists_in_state(vin):
            return { "success": False, "error": "Vehicle does not exist" }

        # 2. Find and invalidate previous active reports for the VIN
        for report in self.history_reports.values():
            if report["vin"] == vin and report["status"] in self._current_report_statuses():
                report["status"] = "invalidated"

        report_data, report_data_str = self._build_report_payload(vin)
        new_report_id = self._next_report_id(vin)
        generated_at = self._next_generated_at(vin)

        # 6. Create and store the new report
        new_report = {
            "report_id": new_report_id,
            "vin": vin,
            "status": "active",
            "generated_at": generated_at,
            "report_data": report_data_str,
        }
        self.history_reports[new_report_id] = new_report

        return {
            "success": True,
            "message": f"Report regenerated for VIN {vin}",
            "report_id": new_report_id,
        }

    def update_report_data(self, report_id: str, new_report_data: str) -> dict:
        """
        Modify the contents (`report_data`) of an existing vehicle history report.

        Args:
            report_id (str): The unique ID of the vehicle history report to update.
            new_report_data (str): The new report data (raw or serialized) to set.

        Returns:
            dict: {
                "success": True,
                "message": "Report data updated."
            }
            or
            {
                "success": False,
                "error": "Report does not exist."
            }

        Constraints:
            - The specified report must already exist in the system.
        """
        report = self.history_reports.get(report_id)
        if not report:
            return { "success": False, "error": "Report does not exist." }

        report["report_data"] = new_report_data
        return { "success": True, "message": "Report data updated." }


    def log_user_report_request(
        self, 
        user_id: str, 
        vin: str, 
        request_time: str, 
        status: str, 
        report_id: str = ""
    ) -> dict:
        """
        Record a new user request for a vehicle history report.

        Args:
            user_id (str): The identifier of the user requesting the report.
            vin (str): The VIN for the target vehicle.
            request_time (str): The time the request is made (ISO8601 string).
            status (str): Status for the request, e.g., 'pending'.
            report_id (str, optional): Associated report ID, can be empty or assigned later.

        Returns:
            dict: 
                - On success: 
                    { "success": True, "message": "User request logged", "request_id": <generated_id> }
                - On failure (VIN does not exist):
                    { "success": False, "error": "VIN does not exist" }

        Constraints:
            - User requests for reports must reference existing VINs in the system.
        """
        if vin not in self.vehicles:
            return { "success": False, "error": "VIN does not exist" }

        request_id = str(uuid.uuid4())
        new_request = {
            "request_id": request_id,
            "user_id": user_id,
            "vin": vin,
            "report_id": report_id,
            "request_time": request_time,
            "status": status
        }
        self.user_requests[request_id] = new_request
        return { "success": True, "message": "User request logged", "request_id": request_id }

    def update_user_request_status(self, request_id: str, new_status: str) -> dict:
        """
        Change the status of a user report request.

        Args:
            request_id (str): The unique identifier for the user request.
            new_status (str): The new status to set for this request (e.g., 'requested', 'fulfilled', etc.).

        Returns:
            dict: 
                - On success: { "success": True, "message": "User request status updated successfully." }
                - On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - The request_id must exist in the user requests map.
        """
        if request_id not in self.user_requests:
            return { "success": False, "error": "User request with the given ID does not exist." }

        self.user_requests[request_id]["status"] = new_status

        return { "success": True, "message": "User request status updated successfully." }

    def associate_report_with_request(self, request_id: str, report_id: str) -> dict:
        """
        Link a generated history report with a specific user request.

        Args:
            request_id (str): The ID of the user request to associate a report with.
            report_id (str): The ID of the generated vehicle history report.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Linked report <report_id> with user request <request_id>"
                    }
                On error:
                    {
                        "success": False,
                        "error": <reason>
                    }

        Constraints:
            - Both request and report must exist.
            - The VIN of the user request must match the VIN of the report.
            - The association is made by setting the report_id field of the user request.
        """
        # Check existence
        if request_id not in self.user_requests:
            return {"success": False, "error": f"User request {request_id} does not exist"}
        if report_id not in self.history_reports:
            return {"success": False, "error": f"Report {report_id} does not exist"}

        user_request = self.user_requests[request_id]
        report = self.history_reports[report_id]

        # VIN match check
        if user_request["vin"] != report["vin"]:
            return {
                "success": False,
                "error": "VIN mismatch between report and request"
            }

        # Perform the association
        user_request["report_id"] = report_id

        return {
            "success": True,
            "message": f"Linked report {report_id} with user request {request_id}"
        }


class VehicleHistoryReportingSystem(BaseEnv):
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

    def get_vehicle_by_vin(self, **kwargs):
        return self._call_inner_tool('get_vehicle_by_vin', kwargs)

    def vehicle_exists(self, **kwargs):
        return self._call_inner_tool('vehicle_exists', kwargs)

    def get_history_report_by_vin(self, **kwargs):
        return self._call_inner_tool('get_history_report_by_vin', kwargs)

    def get_active_history_report_by_vin(self, **kwargs):
        return self._call_inner_tool('get_active_history_report_by_vin', kwargs)

    def get_history_report_by_id(self, **kwargs):
        return self._call_inner_tool('get_history_report_by_id', kwargs)

    def list_reports_by_vin(self, **kwargs):
        return self._call_inner_tool('list_reports_by_vin', kwargs)

    def get_accident_records_by_vin(self, **kwargs):
        return self._call_inner_tool('get_accident_records_by_vin', kwargs)

    def get_ownership_records_by_vin(self, **kwargs):
        return self._call_inner_tool('get_ownership_records_by_vin', kwargs)

    def get_service_records_by_vin(self, **kwargs):
        return self._call_inner_tool('get_service_records_by_vin', kwargs)

    def get_user_request_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_request_by_id', kwargs)

    def get_user_requests_by_vin(self, **kwargs):
        return self._call_inner_tool('get_user_requests_by_vin', kwargs)

    def get_latest_user_request_for_vin(self, **kwargs):
        return self._call_inner_tool('get_latest_user_request_for_vin', kwargs)

    def get_report_status(self, **kwargs):
        return self._call_inner_tool('get_report_status', kwargs)

    def validate_report_includes_all_records(self, **kwargs):
        return self._call_inner_tool('validate_report_includes_all_records', kwargs)

    def create_vehicle_history_report(self, **kwargs):
        return self._call_inner_tool('create_vehicle_history_report', kwargs)

    def update_history_report_status(self, **kwargs):
        return self._call_inner_tool('update_history_report_status', kwargs)

    def regenerate_history_report(self, **kwargs):
        return self._call_inner_tool('regenerate_history_report', kwargs)

    def update_report_data(self, **kwargs):
        return self._call_inner_tool('update_report_data', kwargs)

    def log_user_report_request(self, **kwargs):
        return self._call_inner_tool('log_user_report_request', kwargs)

    def update_user_request_status(self, **kwargs):
        return self._call_inner_tool('update_user_request_status', kwargs)

    def associate_report_with_request(self, **kwargs):
        return self._call_inner_tool('associate_report_with_request', kwargs)
