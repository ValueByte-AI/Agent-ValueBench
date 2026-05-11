# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, Optional, TypedDict
import uuid
from typing import List, Dict



# Represents a food service or processing facility
class FacilityInfo(TypedDict):
    facility_id: str
    name: str
    address: str
    contact_info: str
    compliance_status: str  # based on "compliance_sta"

# Represents a certified inspector
class InspectorInfo(TypedDict):
    inspector_id: str
    name: str
    certification_number: str
    qualifications: str
    contact_info: str
    availability: str  # Could be expanded to a more complex schedule if needed

# Represents a category of inspection check/item
class CheckTypeInfo(TypedDict):
    check_id: str
    name: str
    description: str

# Represents a scheduled inspection session
class InspectionAppointmentInfo(TypedDict):
    appointment_id: str
    facility_id: str
    inspector_id: str
    scheduled_datetime: str
    checks_to_perform: List[str]   # List of check_id
    status: str
    outcome_report_id: Optional[str]  # None if not yet completed

# Documents the outcome of an inspection
class InspectionOutcomeReportInfo(TypedDict):
    outcome_report_id: str
    appointment_id: str
    date_completed: str
    results: str
    compliance_violations: List[str]
    recommendation: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Facilities: {facility_id: FacilityInfo}
        self.facilities: Dict[str, FacilityInfo] = {}
        # Inspectors: {inspector_id: InspectorInfo}
        self.inspectors: Dict[str, InspectorInfo] = {}
        # Inspection Appointments: {appointment_id: InspectionAppointmentInfo}
        self.inspection_appointments: Dict[str, InspectionAppointmentInfo] = {}
        # Check Types: {check_id: CheckTypeInfo}
        self.check_types: Dict[str, CheckTypeInfo] = {}
        # Inspection Outcome Reports: {outcome_report_id: InspectionOutcomeReportInfo}
        self.inspection_outcome_reports: Dict[str, InspectionOutcomeReportInfo] = {}

        # Constraints:
        # - An inspector must have a valid (current and appropriate) certification to be assigned to an inspection.
        # - No inspector or facility can be double-booked for overlapping appointments.
        # - Each inspection appointment must specify at least one check type (from CheckType).
        # - Inspections must be linked to existing, registered facilities and inspectors.
        # - Outcome reports are generated only after inspection appointments are completed.

    @staticmethod
    def _has_meaningful_outcome_report_id(appointment: dict) -> bool:
        outcome_report_id = appointment.get("outcome_report_id")
        if outcome_report_id is None:
            return False
        if isinstance(outcome_report_id, str) and outcome_report_id.strip().lower() in {"", "none", "null", "n/a"}:
            return False
        return bool(outcome_report_id)

    def get_facility_by_id(self, facility_id: str) -> dict:
        """
        Retrieve information for a facility by its facility_id.

        Args:
            facility_id (str): The unique ID of the facility to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": FacilityInfo,
            }
            or
            {
                "success": False,
                "error": str  # if the facility_id is not found
            }

        Constraints:
            - The facility_id must exist in the system.
        """
        facility = self.facilities.get(facility_id)
        if facility is None:
            return { "success": False, "error": "Facility not found" }

        return { "success": True, "data": facility }

    def get_facility_by_name(self, name: str) -> dict:
        """
        Retrieve information for a facility by its name.

        Args:
            name (str): The name of the facility to search.

        Returns:
            dict: 
                { "success": True, "data": FacilityInfo }
                OR
                { "success": False, "error": "Facility not found" }

        Constraints:
            - Facility names are assumed to be unique; if multiple found, return the first match.
        """
        for facility in self.facilities.values():
            if facility["name"] == name:
                return { "success": True, "data": facility }
        return { "success": False, "error": "Facility not found" }

    def list_facilities(self) -> dict:
        """
        Retrieve a list of all registered facilities.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[FacilityInfo]  # List of facility info dictionaries (may be empty)
            }

        Constraints:
            - No particular constraints for query operation.
        """
        facilities_list = list(self.facilities.values())
        return { "success": True, "data": facilities_list }

    def get_inspector_by_name(self, name: str) -> dict:
        """
        Retrieve inspector(s) information by their name.

        Args:
            name (str): The exact name of the inspector to search for.

        Returns:
            dict: {
                "success": True,
                "data": List[InspectorInfo]  # List of all matching inspectors (empty if none found)
            }
            or
            {
                "success": False,
                "error": str  # Error description
            }

        Notes/Constraints:
            - The search is case-sensitive and matches the 'name' field exactly.
            - There may be multiple inspectors with the same name in the system.
        """
        if not isinstance(name, str) or not name.strip():
            return {"success": False, "error": "Invalid inspector name provided."}

        matching = [
            inspector_info
            for inspector_info in self.inspectors.values()
            if inspector_info["name"] == name
        ]
        return {"success": True, "data": matching}

    def get_inspector_by_id(self, inspector_id: str) -> dict:
        """
        Retrieve an inspector’s information using their unique inspector_id.

        Args:
            inspector_id (str): The unique identifier of the inspector.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": InspectorInfo  # Inspector's metadata
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Inspector not found"
                    }

        Constraints:
            - The inspector_id must refer to an inspector present in the system.
        """
        if not inspector_id or inspector_id not in self.inspectors:
            return {"success": False, "error": "Inspector not found"}

        return {"success": True, "data": self.inspectors[inspector_id]}

    def list_inspectors(self) -> dict:
        """
        Retrieve details of all inspectors in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[InspectorInfo]  # All inspector records (may be empty)
            }
        No constraints or preconditions.
        """
        inspector_list = list(self.inspectors.values())
        return {
            "success": True,
            "data": inspector_list
        }

    def check_inspector_certification_status(self, inspector_id: str) -> dict:
        """
        Verify if the inspector holds a valid and appropriate certification.

        Args:
            inspector_id (str): The unique ID of the inspector.

        Returns:
            dict:
                If inspector exists:
                    {
                        "success": True,
                        "data": {
                            "inspector_id": str,
                            "certification_valid": bool,
                            "certification_number": str,
                            "qualifications": str
                        }
                    }
                If inspector does not exist:
                    {
                        "success": False,
                        "error": "Inspector not found"
                    }

        Constraints:
            - Inspector must exist in the system.
            - "Valid certification" means the inspector has a non-empty certification_number.
        """
        inspector = self.inspectors.get(inspector_id)
        if inspector is None:
            return {
                "success": False,
                "error": "Inspector not found"
            }

        # Valid if certification_number is a non-empty string
        cert_num = inspector.get("certification_number", "")
        valid = bool(cert_num and cert_num.strip())
        return {
            "success": True,
            "data": {
                "inspector_id": inspector_id,
                "certification_valid": valid,
                "certification_number": cert_num,
                "qualifications": inspector.get("qualifications", "")
            }
        }

    def get_inspector_availability(self, inspector_id: str) -> dict:
        """
        Obtain all inspection appointments assigned to a given inspector.
    
        Args:
            inspector_id (str): Unique ID of the inspector whose appointments/schedule is requested.

        Returns:
            dict: {
                "success": True,
                "data": List[InspectionAppointmentInfo],
            }
            or
            {
                "success": False,
                "error": str  # e.g., Inspector does not exist
            }

        Constraints:
            - The inspector_id must correspond to a registered inspector.
            - Returns all appointments for the inspector (regardless of status).
        """
        if inspector_id not in self.inspectors:
            return { "success": False, "error": "Inspector does not exist" }

        appointments = [
            appointment
            for appointment in self.inspection_appointments.values()
            if appointment["inspector_id"] == inspector_id
        ]

        return { "success": True, "data": appointments }

    def get_facility_appointments(self, facility_id: str) -> dict:
        """
        Retrieve all inspection appointments scheduled for a particular facility.

        Args:
            facility_id (str): The unique identifier for the target facility.

        Returns:
            dict: {
                "success": True,
                "data": List[InspectionAppointmentInfo]  # List of appointments for this facility
            }
            or
            {
                "success": False,
                "error": str  # Error description, e.g. "Facility not found"
            }

        Constraints:
            - Facility must exist in the system.
            - Returns empty list if facility has no scheduled appointments.
        """
        if facility_id not in self.facilities:
            return { "success": False, "error": "Facility not found" }

        appointments = [
            appt for appt in self.inspection_appointments.values()
            if appt["facility_id"] == facility_id
        ]

        return { "success": True, "data": appointments }

    def get_appointments_by_datetime(
        self, 
        target_datetime: str, 
        inspector_id: str = None, 
        facility_id: str = None
    ) -> dict:
        """
        Retrieve inspection appointments scheduled at a specific datetime,
        optionally filtered by inspector_id and/or facility_id.

        Args:
            target_datetime (str): The scheduled datetime to search for (format as stored in system).
            inspector_id (str, optional): If provided, only appointments for this inspector will be returned.
            facility_id (str, optional): If provided, only appointments for this facility will be returned.

        Returns:
            dict:
                On success: {
                    "success": True,
                    "data": List[InspectionAppointmentInfo]  # may be empty
                }
                On error: {
                    "success": False,
                    "error": str
                }
        Constraints:
            - Only appointments with scheduled_datetime exactly matching target_datetime are returned.
            - If inspector_id or facility_id is provided, output is further filtered by those.
            - No error if no results or filter keys don't exist.
        """
        # Collect matching appointments
        results = []
        for appointment in self.inspection_appointments.values():
            if appointment['scheduled_datetime'] != target_datetime:
                continue
            if inspector_id is not None and appointment['inspector_id'] != inspector_id:
                continue
            if facility_id is not None and appointment['facility_id'] != facility_id:
                continue
            results.append(appointment)

        return { "success": True, "data": results }

    def get_check_type_by_name(self, name: str) -> dict:
        """
        Retrieve the check type (check_id, name, description) by its name.

        Args:
            name (str): The name of the check type to look up.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": CheckTypeInfo
                }
                or
                {
                    "success": False,
                    "error": "<reason>"
                }
        Constraints:
            - Name must match exactly as stored in the system (case sensitive).
            - Returns the first match found.
        """
        if not name or not isinstance(name, str):
            return {"success": False, "error": "Invalid or missing check type name"}
    
        for check_type in self.check_types.values():
            if check_type["name"] == name:
                return {"success": True, "data": check_type}
    
        return {"success": False, "error": f"No check type found with name: {name}"}

    def list_check_types(self) -> dict:
        """
        List all available types of inspection checks.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[CheckTypeInfo],  # All check types, empty list if none exist
            }
        """
        result = list(self.check_types.values())
        return { "success": True, "data": result }

    def get_appointment_by_id(self, appointment_id: str) -> dict:
        """
        Retrieve details for a specific inspection appointment.

        Args:
            appointment_id (str): The unique identifier of the inspection appointment.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": InspectionAppointmentInfo
                    }
                - On failure (appointment not found):
                    {
                        "success": False,
                        "error": "Appointment not found"
                    }

        Constraints:
            - The appointment_id must exist in the system.
        """
        appointment = self.inspection_appointments.get(appointment_id)
        if appointment is None:
            return { "success": False, "error": "Appointment not found" }
        return { "success": True, "data": appointment }

    def get_appointments_for_inspector(self, inspector_id: str) -> dict:
        """
        Retrieve all inspection appointments (with metadata) assigned to a specific inspector.

        Args:
            inspector_id (str): The ID of the inspector.

        Returns:
            dict: 
                On success:
                    {
                      "success": True,
                      "data": List[InspectionAppointmentInfo]
                    }
                On failure:
                    {
                      "success": False,
                      "error": str
                    }

        Constraints:
            - The inspector_id must correspond to an existing inspector.
        """
        if inspector_id not in self.inspectors:
            return { "success": False, "error": "Inspector does not exist" }

        appointments = [
            appt for appt in self.inspection_appointments.values()
            if appt["inspector_id"] == inspector_id
        ]
        return { "success": True, "data": appointments }

    def get_inspection_outcome_report_by_id(self, outcome_report_id: str) -> dict:
        """
        Retrieve a completed inspection outcome report by its outcome_report_id.

        Args:
            outcome_report_id (str): Unique identifier for the inspection outcome report.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": InspectionOutcomeReportInfo
                    }
                - On failure:
                    {
                        "success": False,
                        "error": "Outcome report not found"
                    }

        Constraints:
            - The outcome_report_id must exist in the inspection outcome reports registry.
        """
        report = self.inspection_outcome_reports.get(outcome_report_id)
        if not report:
            return { "success": False, "error": "Outcome report not found" }
        return { "success": True, "data": report }

    def get_appointments_by_status(self, status: str) -> dict:
        """
        Retrieves all inspection appointments filtered by their current status.

        Args:
            status (str): The appointment status to filter by. Example: "Scheduled", "Completed", "Cancelled".

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[InspectionAppointmentInfo],  # matching appointments, may be empty
                }
                OR
                {
                    "success": False,
                    "error": str  # reason for failure (e.g., missing status)
                }

        Constraints:
            - No validation on allowed status values is specified.
            - Returns all matching appointments, or empty list if none.
        """
        if not status or not isinstance(status, str):
            return {"success": False, "error": "Status parameter must be a non-empty string."}

        matching_appointments = [
            appointment for appointment in self.inspection_appointments.values()
            if appointment.get("status") == status
        ]
        return {"success": True, "data": matching_appointments}

    def schedule_inspection_appointment(
        self, 
        facility_id: str, 
        inspector_id: str, 
        scheduled_datetime: str, 
        checks_to_perform: list
    ) -> dict:
        """
        Schedule a new inspection appointment for a facility, assigning an inspector, date/time, and one or more check types.

        Args:
            facility_id (str): The ID of the facility to inspect.
            inspector_id (str): The ID of the inspector to assign.
            scheduled_datetime (str): When the inspection is to occur (ISO 8601 recommended).
            checks_to_perform (list): List of check_id strings specifying what should be checked.

        Returns:
            dict: 
              On success: {
                  'success': True,
                  'message': 'Inspection appointment scheduled successfully.',
                  'appointment': <InspectionAppointmentInfo>
              }
              On failure: {
                  'success': False,
                  'error': <reason>
              }

        Constraints enforced:
            - Facility and inspector must exist.
            - Inspector must have a valid/current/appropriate certification.
            - No inspector or facility can be double-booked for overlapping appointments.
            - At least one valid check_id is required and all must exist in check_types.
        """
        # 1. Facility exists
        if facility_id not in self.facilities:
            return {'success': False, 'error': 'Facility does not exist.'}

        # 2. Inspector exists
        if inspector_id not in self.inspectors:
            return {'success': False, 'error': 'Inspector does not exist.'}

        # 3. Inspector certification valid
        cert_status = self.check_inspector_certification_status(inspector_id)
        if (not isinstance(cert_status, dict)) or (not cert_status.get('success', False)):
            return {'success': False, 'error': 'Cannot verify inspector certification.'}
        cert_data = cert_status.get("data", {})
        if not cert_data.get("certification_valid", False):
            return {'success': False, 'error': 'Inspector does not have a valid certification.'}

        # 4. At least one check, and all check_ids exist
        if not checks_to_perform or not isinstance(checks_to_perform, list):
            return {'success': False, 'error': 'At least one check_id must be provided.'}
        for check_id in checks_to_perform:
            if check_id not in self.check_types:
                return {'success': False, 'error': f'Check type ID {check_id} does not exist.'}

        # 5. Inspector and facility not double-booked at scheduled_datetime
        for app in self.inspection_appointments.values():
            if app['scheduled_datetime'] == scheduled_datetime:
                if app['inspector_id'] == inspector_id:
                    return {'success': False, 'error': 'Inspector double-booked for this time.'}
                if app['facility_id'] == facility_id:
                    return {'success': False, 'error': 'Facility double-booked for this time.'}

        # 6. Generate unique appointment_id
        appointment_id = str(uuid.uuid4())

        # 7. Create appointment
        appointment: InspectionAppointmentInfo = {
            "appointment_id": appointment_id,
            "facility_id": facility_id,
            "inspector_id": inspector_id,
            "scheduled_datetime": scheduled_datetime,
            "checks_to_perform": list(checks_to_perform),
            "status": "scheduled",
            "outcome_report_id": None
        }
        self.inspection_appointments[appointment_id] = appointment

        return {
            "success": True,
            "message": "Inspection appointment scheduled successfully.",
            "appointment": appointment
        }

    def update_appointment_status(self, appointment_id: str, new_status: str) -> dict:
        """
        Change the status of an inspection appointment.

        Args:
            appointment_id (str): The unique ID of the inspection appointment.
            new_status (str): The new status to set (e.g., "scheduled", "completed", "cancelled").

        Returns:
            dict: {
                "success": True,
                "message": "Appointment status updated successfully."
            }
            or
            {
                "success": False,
                "error": "Reason for failure"
            }

        Constraints:
            - The appointment must exist.
            - Status transitions may be constrained by business logic. (Here, we allow all transitions.)
            - (Optionally) Disallow updating status for already cancelled appointments.
        """
        if appointment_id not in self.inspection_appointments:
            return { "success": False, "error": "Appointment does not exist." }

        appointment = self.inspection_appointments[appointment_id]

        # Optional: Disallow updates if appointment is already cancelled
        if appointment["status"] == "cancelled":
            return { "success": False, "error": "Cannot change status of a cancelled appointment." }

        # Optional: Disallow redundant status update
        if appointment["status"] == new_status:
            return { "success": False, "error": "Appointment already in the given status." }

        appointment["status"] = new_status
        self.inspection_appointments[appointment_id] = appointment

        return { "success": True, "message": "Appointment status updated successfully." }

    def assign_checks_to_appointment(self, appointment_id: str, check_ids: list) -> dict:
        """
        Add or update the list of check types for a given inspection appointment.

        Args:
            appointment_id (str): The ID of the inspection appointment to update.
            check_ids (list of str): List of check type IDs to assign to this appointment.

        Returns:
            dict: 
                On success:
                    { "success": True, "message": "Check types updated for appointment <appointment_id>" }
                On error:
                    { "success": False, "error": "reason" }

        Constraints:
            - The appointment must exist.
            - check_ids must not be empty (appointment must have at least one check type).
            - All provided check_ids must exist in self.check_types.
        """
        # Check appointment exists
        if appointment_id not in self.inspection_appointments:
            return { "success": False, "error": "Appointment does not exist" }
        # Check non-empty check_ids
        if not check_ids or not isinstance(check_ids, list):
            return { "success": False, "error": "At least one check type must be assigned" }
        # Check all check_ids valid
        invalid_ids = [cid for cid in check_ids if cid not in self.check_types]
        if invalid_ids:
            return { "success": False, "error": f"Invalid check_id(s): {', '.join(invalid_ids)}" }

        # Perform update
        self.inspection_appointments[appointment_id]['checks_to_perform'] = check_ids

        return {
            "success": True,
            "message": f"Check types updated for appointment {appointment_id}"
        }


    def generate_inspection_outcome_report(
        self, 
        appointment_id: str, 
        date_completed: str, 
        results: str, 
        compliance_violations: List[str], 
        recommendation: str
    ) -> dict:
        """
        Create and link an outcome report to a completed inspection appointment.

        Args:
            appointment_id (str): The appointment to attach the outcome report to.
            date_completed (str): Date/time when the inspection was completed.
            results (str): Narrative/summary of findings.
            compliance_violations (List[str]): List of compliance violations identified.
            recommendation (str): Recommendations proposed by the inspector.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Outcome report generated and linked.",
                        "outcome_report_id": <report_id>
                    }
                On failure:
                    {
                        "success": False,
                        "error": <reason>
                    }

        Constraints:
            - Only for appointments with status 'completed'.
            - Cannot overwrite existing outcome_report for this appointment.
            - All essential report fields must be provided.
        """
        appointment = self.inspection_appointments.get(appointment_id)
        if not appointment:
            return {"success": False, "error": "Appointment does not exist."}

        if appointment["status"] != "completed":
            return {"success": False, "error": "Appointment is not completed; outcome report cannot be generated."}
    
        if self._has_meaningful_outcome_report_id(appointment):
            return {"success": False, "error": "Outcome report already exists for this appointment."}
    
        if not results or not date_completed or not isinstance(compliance_violations, list) or recommendation is None:
            return {"success": False, "error": "All report fields must be provided and valid."}

        # Generate a new unique outcome_report_id
        outcome_report_id = str(uuid.uuid4())

        # Build and save the report
        report = {
            "outcome_report_id": outcome_report_id,
            "appointment_id": appointment_id,
            "date_completed": date_completed,
            "results": results,
            "compliance_violations": compliance_violations,
            "recommendation": recommendation
        }
        self.inspection_outcome_reports[outcome_report_id] = report

        # Link to appointment
        self.inspection_appointments[appointment_id]["outcome_report_id"] = outcome_report_id

        return {
            "success": True,
            "message": "Outcome report generated and linked.",
            "outcome_report_id": outcome_report_id
        }

    def edit_inspection_appointment(
        self,
        appointment_id: str,
        scheduled_datetime: str = None,
        inspector_id: str = None,
        checks_to_perform: list = None
    ) -> dict:
        """
        Modify the details (scheduled date/time, assigned inspector, and/or checks to perform)
        of an existing inspection appointment.

        Args:
            appointment_id (str): The ID of the appointment to edit.
            scheduled_datetime (str, optional): New scheduled datetime (if changing).
            inspector_id (str, optional): New inspector ID to assign (if changing).
            checks_to_perform (list of str, optional): List of check IDs to perform (if changing).

        Returns:
            dict: {
                "success": True,
                "message": "Inspection appointment updated"
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - appointment_id must exist.
            - inspector_id (if changing) must exist and hold valid certification.
            - checks_to_perform (if changing) must be non-empty and valid check_ids.
            - No double-booking for inspector or facility at scheduled_datetime.
        """
        # Fetch existing appointment
        appt = self.inspection_appointments.get(appointment_id)
        if not appt:
            return { "success": False, "error": "Appointment not found" }

        # Prepare new values (default to existing if not changed)
        new_datetime = scheduled_datetime if scheduled_datetime is not None else appt["scheduled_datetime"]
        new_inspector_id = inspector_id if inspector_id is not None else appt["inspector_id"]
        new_checks = checks_to_perform if checks_to_perform is not None else appt["checks_to_perform"]
        facility_id = appt["facility_id"]

        # 1. Inspector validation (if changing)
        inspector_info = self.inspectors.get(new_inspector_id)
        if not inspector_info:
            return { "success": False, "error": "Inspector does not exist" }

        # Here, for certification, assume 'certification_number' must not be empty (could be expanded)
        if not inspector_info["certification_number"]:
            return { "success": False, "error": "Inspector lacks valid certification" }

        # 2. CheckType validation
        if not new_checks or not isinstance(new_checks, list):
            return { "success": False, "error": "No checks specified for inspection" }
        for cid in new_checks:
            if cid not in self.check_types:
                return { "success": False, "error": f"Invalid check type: {cid}" }

        # 3. Double-booking check (inspector and facility for overlapping appointments)
        for other_id, other in self.inspection_appointments.items():
            if other_id == appointment_id:
                continue  # skip self
            # Only consider appointments that are still scheduled (not canceled/completed)
            if other["status"] == "cancelled":
                continue
            # Conflict if same inspector and same datetime
            if other["inspector_id"] == new_inspector_id and other["scheduled_datetime"] == new_datetime:
                return { "success": False, "error": "Inspector is already booked for that date/time" }
            # Conflict if same facility and same datetime
            if other["facility_id"] == facility_id and other["scheduled_datetime"] == new_datetime:
                return { "success": False, "error": "Facility is already booked for that date/time" }

        # 4. Commit changes
        appt["scheduled_datetime"] = new_datetime
        appt["inspector_id"] = new_inspector_id
        appt["checks_to_perform"] = new_checks
        self.inspection_appointments[appointment_id] = appt

        return { "success": True, "message": "Inspection appointment updated" }

    def cancel_inspection_appointment(self, appointment_id: str) -> dict:
        """
        Cancel or remove an inspection appointment, freeing up any inspector/facility time slots.

        Args:
            appointment_id (str): The unique ID of the inspection appointment to cancel.

        Returns:
            dict: {
                "success": True,
                "message": "Appointment <id> cancelled and removed."
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - Cannot cancel a non-existent appointment.
            - Cannot cancel an appointment that is already completed (i.e., has an outcome report generated).
            - Cancelling frees up any time slots for the inspector/facility.
            - Appointments that are 'already cancelled' (if status is tracked) are treated as missing/removable.
        """
        appointment = self.inspection_appointments.get(appointment_id)
        if not appointment:
            return {"success": False, "error": "Appointment does not exist."}
        if str(appointment.get("status", "")).strip().lower() == "completed" or self._has_meaningful_outcome_report_id(appointment):
            return {"success": False, "error": "Cannot cancel a completed appointment (outcome already reported)."}

        # Remove the appointment
        del self.inspection_appointments[appointment_id]
        return {
            "success": True,
            "message": f"Appointment {appointment_id} cancelled and removed."
        }

    def add_facility(
        self, 
        facility_id: str, 
        name: str, 
        address: str, 
        contact_info: str, 
        compliance_status: str
    ) -> dict:
        """
        Register a new facility into the system.

        Args:
            facility_id (str): Unique ID for the facility.
            name (str): Facility name.
            address (str): Physical address of the facility.
            contact_info (str): Contact information for the facility.
            compliance_status (str): Initial compliance status for the facility.

        Returns:
            dict: 
                On success: {"success": True, "message": "Facility registered successfully."}
                On failure: {"success": False, "error": <reason>}

        Constraints:
            - facility_id must be unique — must not already exist in self.facilities.
            - All parameters must be provided and non-empty.
        """
        # Basic validation
        if not all([facility_id, name, address, contact_info, compliance_status]):
            return {"success": False, "error": "Missing or invalid input fields."}

        # Check for unique facility_id
        if facility_id in self.facilities:
            return {"success": False, "error": "Facility with this ID already exists."}

        # Prepare new facility info
        new_facility = {
            "facility_id": facility_id,
            "name": name,
            "address": address,
            "contact_info": contact_info,
            "compliance_status": compliance_status
        }

        self.facilities[facility_id] = new_facility

        return {"success": True, "message": "Facility registered successfully."}

    def add_inspector(
        self,
        inspector_id: str,
        name: str,
        certification_number: str,
        qualifications: str,
        contact_info: str,
        availability: str
    ) -> dict:
        """
        Register a new inspector with the specified details.

        Args:
            inspector_id (str): Unique identifier for the inspector.
            name (str): Inspector's full name.
            certification_number (str): Inspector's certification/license number.
            qualifications (str): String describing inspector's specific qualifications.
            contact_info (str): Contact information for the inspector.
            availability (str): Inspector's availability timing/schedule.

        Returns:
            dict: {
                "success": True,
                "message": "Inspector successfully added."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - inspector_id must be unique.
            - All parameters must be provided and not empty.
        """
        # Check for uniqueness
        if inspector_id in self.inspectors:
            return { "success": False, "error": "Inspector ID already exists." }
    
        # Check for required values (simple blank/None check)
        required_fields = {
            "inspector_id": inspector_id,
            "name": name,
            "certification_number": certification_number,
            "qualifications": qualifications,
            "contact_info": contact_info,
            "availability": availability,
        }
        for field, value in required_fields.items():
            if value is None or (isinstance(value, str) and value.strip() == ""):
                return { "success": False, "error": f"Missing or empty field: {field}" }

        # Create and add the inspector
        inspector_info: InspectorInfo = {
            "inspector_id": inspector_id,
            "name": name,
            "certification_number": certification_number,
            "qualifications": qualifications,
            "contact_info": contact_info,
            "availability": availability
        }
        self.inspectors[inspector_id] = inspector_info

        return { "success": True, "message": "Inspector successfully added." }

    def add_check_type(self, check_id: str, name: str, description: str) -> dict:
        """
        Add a new inspection check type/category to the system.

        Args:
            check_id (str): Unique identifier for the check type.
            name (str): Category name (e.g., "Temperature").
            description (str): Description of the check type.

        Returns:
            dict: {
                "success": True,
                "message": "Check type '<name>' added successfully."
            }
            OR
            {
                "success": False,
                "error": <reason string>
            }

        Constraints:
            - check_id must be unique (not already present in self.check_types).
            - All parameters must be non-empty strings.
        """
        if not check_id or not name or not description:
            return {"success": False, "error": "All parameters (check_id, name, description) must be provided and non-empty."}

        if check_id in self.check_types:
            return {"success": False, "error": "Check type with ID already exists."}

        self.check_types[check_id] = {
            "check_id": check_id,
            "name": name,
            "description": description,
        }

        return {"success": True, "message": f"Check type '{name}' added successfully."}

    def update_inspector_certification(
        self,
        inspector_id: str,
        certification_number: str = None,
        qualifications: str = None
    ) -> dict:
        """
        Modify or update an inspector’s certification info or validity.

        Args:
            inspector_id (str): The unique ID of the inspector to update.
            certification_number (str, optional): The new certification number.
            qualifications (str, optional): The new or updated qualification information.

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "message": "Inspector certification info updated"
                }
                On failure: {
                    "success": False,
                    "error": str  # reason for error
                }
        Constraints:
            - Inspector must exist in the system.
            - At least one updatable field must be provided.
        """
        inspector = self.inspectors.get(inspector_id)
        if inspector is None:
            return {"success": False, "error": "Inspector not found"}

        # Track whether we perform any update
        updated = False

        if certification_number is not None:
            inspector["certification_number"] = certification_number
            updated = True

        if qualifications is not None:
            inspector["qualifications"] = qualifications
            updated = True

        if not updated:
            return {"success": False, "error": "No certification info provided to update"}

        # Save the inspector back (not strictly necessary since dicts are mutable, but explicit)
        self.inspectors[inspector_id] = inspector

        return {"success": True, "message": "Inspector certification info updated"}

    def update_facility_compliance_status(self, facility_id: str, new_status: str) -> dict:
        """
        Update the compliance status of the specified facility.

        Args:
            facility_id (str): The unique identifier of the facility whose status will be updated.
            new_status (str): The new compliance status string to assign.

        Returns:
            dict: {
                "success": True,
                "message": "Facility compliance status updated successfully."
            }
            or
            {
                "success": False,
                "error": "Facility not found."
            }

        Constraints:
            - The facility must exist in the system.
        """
        if facility_id not in self.facilities:
            return { "success": False, "error": "Facility not found." }
    
        self.facilities[facility_id]["compliance_status"] = new_status
        return { "success": True, "message": "Facility compliance status updated successfully." }


class FoodSafetyInspectionManagementSystem(BaseEnv):
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
            if key == "check_inspector_certification_status":
                setattr(env, "_check_inspector_certification_status_state", copy.deepcopy(value))
                continue
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

    def get_facility_by_id(self, **kwargs):
        return self._call_inner_tool('get_facility_by_id', kwargs)

    def get_facility_by_name(self, **kwargs):
        return self._call_inner_tool('get_facility_by_name', kwargs)

    def list_facilities(self, **kwargs):
        return self._call_inner_tool('list_facilities', kwargs)

    def get_inspector_by_name(self, **kwargs):
        return self._call_inner_tool('get_inspector_by_name', kwargs)

    def get_inspector_by_id(self, **kwargs):
        return self._call_inner_tool('get_inspector_by_id', kwargs)

    def list_inspectors(self, **kwargs):
        return self._call_inner_tool('list_inspectors', kwargs)

    def check_inspector_certification_status(self, **kwargs):
        return self._call_inner_tool('check_inspector_certification_status', kwargs)

    def get_inspector_availability(self, **kwargs):
        return self._call_inner_tool('get_inspector_availability', kwargs)

    def get_facility_appointments(self, **kwargs):
        return self._call_inner_tool('get_facility_appointments', kwargs)

    def get_appointments_by_datetime(self, **kwargs):
        return self._call_inner_tool('get_appointments_by_datetime', kwargs)

    def get_check_type_by_name(self, **kwargs):
        return self._call_inner_tool('get_check_type_by_name', kwargs)

    def list_check_types(self, **kwargs):
        return self._call_inner_tool('list_check_types', kwargs)

    def get_appointment_by_id(self, **kwargs):
        return self._call_inner_tool('get_appointment_by_id', kwargs)

    def get_appointments_for_inspector(self, **kwargs):
        return self._call_inner_tool('get_appointments_for_inspector', kwargs)

    def get_inspection_outcome_report_by_id(self, **kwargs):
        return self._call_inner_tool('get_inspection_outcome_report_by_id', kwargs)

    def get_appointments_by_status(self, **kwargs):
        return self._call_inner_tool('get_appointments_by_status', kwargs)

    def schedule_inspection_appointment(self, **kwargs):
        return self._call_inner_tool('schedule_inspection_appointment', kwargs)

    def update_appointment_status(self, **kwargs):
        return self._call_inner_tool('update_appointment_status', kwargs)

    def assign_checks_to_appointment(self, **kwargs):
        return self._call_inner_tool('assign_checks_to_appointment', kwargs)

    def generate_inspection_outcome_report(self, **kwargs):
        return self._call_inner_tool('generate_inspection_outcome_report', kwargs)

    def edit_inspection_appointment(self, **kwargs):
        return self._call_inner_tool('edit_inspection_appointment', kwargs)

    def cancel_inspection_appointment(self, **kwargs):
        return self._call_inner_tool('cancel_inspection_appointment', kwargs)

    def add_facility(self, **kwargs):
        return self._call_inner_tool('add_facility', kwargs)

    def add_inspector(self, **kwargs):
        return self._call_inner_tool('add_inspector', kwargs)

    def add_check_type(self, **kwargs):
        return self._call_inner_tool('add_check_type', kwargs)

    def update_inspector_certification(self, **kwargs):
        return self._call_inner_tool('update_inspector_certification', kwargs)

    def update_facility_compliance_status(self, **kwargs):
        return self._call_inner_tool('update_facility_compliance_status', kwargs)
