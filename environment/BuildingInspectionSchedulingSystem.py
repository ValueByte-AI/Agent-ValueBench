# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import json
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Optional
import re



class BuildingInfo(TypedDict):
    building_id: str
    address: str
    owner: str
    building_type: str
    compliance_status: str

class InspectorInfo(TypedDict):
    inspector_id: str
    name: str
    contact_info: str
    qualifications: List[str]
    current_status: str

class InspectionAppointmentInfo(TypedDict):
    appointment_id: str
    building_id: str
    inspector_id: str
    scheduled_date: str  # ISO datetime as string
    status: str
    results: Optional[str]
    notes: Optional[str]

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment representing a building inspection scheduling system.
        """
        # Buildings: {building_id: BuildingInfo}
        self.buildings: Dict[str, BuildingInfo] = {}
        # Inspectors: {inspector_id: InspectorInfo}
        self.inspectors: Dict[str, InspectorInfo] = {}
        # Inspection appointments: {appointment_id: InspectionAppointmentInfo}
        self.appointments: Dict[str, InspectionAppointmentInfo] = {}

        # Constraints:
        # - An inspector cannot be assigned to multiple inspections at the same date and time.
        # - An appointment must be associated with valid existing building and inspector entities.
        # - Inspection status must be tracked (e.g., scheduled, completed, cancelled).
        # - Scheduled appointments must not violate inspector qualifications or other eligibility requirements.

    def get_building_by_id(self, building_id: str) -> dict:
        """
        Retrieve detailed information for a specific building via building_id.

        Args:
            building_id (str): The unique identifier of the building.

        Returns:
            dict: {
                "success": True,
                "data": BuildingInfo
            } if found,
            or
            {
                "success": False,
                "error": str
            } if not found.

        Constraints:
            - The building_id must exist in the system to return info.
        """
        building = self.buildings.get(building_id)
        if building is None:
            return {"success": False, "error": "Building does not exist"}

        return {"success": True, "data": building}

    def list_all_buildings(self) -> dict:
        """
        Retrieve a list of all registered buildings in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[BuildingInfo],  # List of all building info dictionaries (empty list if none registered)
            }
        """
        buildings_list = list(self.buildings.values())
        return { "success": True, "data": buildings_list }

    def get_inspector_by_id(self, inspector_id: str) -> dict:
        """
        Retrieve detailed information for a specific inspector by their inspector_id.

        Args:
            inspector_id (str): The unique identifier for the inspector.

        Returns:
            dict:
                - If inspector exists:
                    {
                        "success": True,
                        "data": InspectorInfo
                    }
                - If inspector not found:
                    {
                        "success": False,
                        "error": "Inspector not found"
                    }

        Constraints:
            - The inspector_id must exist in the system.
        """
        inspector = self.inspectors.get(inspector_id)
        if inspector is None:
            return { "success": False, "error": "Inspector not found" }
        return { "success": True, "data": inspector }

    def list_all_inspectors(self) -> dict:
        """
        Retrieve a list of all inspectors in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[InspectorInfo]  # List of inspector info dicts (possibly empty)
            }
        """
        return {
            "success": True,
            "data": list(self.inspectors.values())
        }

    def check_inspector_qualifications(self, inspector_id: str) -> dict:
        """
        Get the list of qualifications for a given inspector.

        Args:
            inspector_id (str): The unique identifier of the inspector.

        Returns:
            dict: {
                "success": True,
                "data": List[str]  # List of inspector's qualifications
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g. inspector not found
            }

        Constraints:
            - The inspector must exist in the system.
        """
        inspector = self.inspectors.get(inspector_id)
        if inspector is None:
            return {"success": False, "error": "Inspector not found"}

        return {"success": True, "data": inspector["qualifications"]}

    def get_building_required_qualifications(self, building_id: str) -> dict:
        """
        Retrieve the required or recommended inspector qualifications for a given building,
        inferred from its building_type and/or compliance_status.
    
        Args:
            building_id (str): The unique identifier for the building.
    
        Returns:
            dict: {
                "success": True,
                "data": List[str],  # List of required/recommended qualifications
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (e.g., building not found)
            }
        """
        building = self.buildings.get(building_id)
        if not building:
            return { "success": False, "error": "Building not found" }

        building_type = building.get("building_type", "").lower()
        compliance_status = building.get("compliance_status", "").lower()

        qualification_rules_text = getattr(self, "_qualification_rules_text", None)
        if isinstance(qualification_rules_text, str) and qualification_rules_text.strip():
            stripped_rules = qualification_rules_text.strip()
            if stripped_rules.lower().startswith("mapping:"):
                stripped_rules = stripped_rules.split(":", 1)[1].strip()

            def _normalize_quals(raw_value):
                if isinstance(raw_value, str):
                    return [
                        token.strip().strip(".")
                        for token in re.split(r"[,/]", raw_value)
                        if token.strip()
                    ]
                if isinstance(raw_value, list):
                    return [str(token).strip() for token in raw_value if str(token).strip()]
                return []

            if stripped_rules.startswith("{"):
                try:
                    parsed_json_rules = json.loads(stripped_rules)
                except Exception:
                    parsed_json_rules = None
                if isinstance(parsed_json_rules, dict):
                    normalized_lookup = {
                        str(key).strip().lower(): _normalize_quals(value)
                        for key, value in parsed_json_rules.items()
                    }
                    for lookup_key in (building_id.lower(), building_type.lower()):
                        quals = normalized_lookup.get(lookup_key)
                        if quals:
                            return {"success": True, "data": quals}

            if "requires" not in stripped_rules.lower():
                bare_quals = _normalize_quals(stripped_rules)
                if bare_quals:
                    return {"success": True, "data": bare_quals}

            parsed_rules = {}
            for segment in stripped_rules.split(";"):
                segment = segment.strip()
                if not segment:
                    continue
                match = re.search(r"(.+?)\s+requires\s+(.+)", segment, flags=re.IGNORECASE)
                if not match:
                    continue
                rule_building_type = match.group(1).strip().lower()
                quals = _normalize_quals(match.group(2))
                if quals:
                    parsed_rules[rule_building_type] = quals
            for lookup_key in (building_id.lower(), building_type.lower()):
                if lookup_key in parsed_rules:
                    return {"success": True, "data": parsed_rules[lookup_key]}
    
        # Example mapping rules for demonstration
        qualification_map = {
            "hospital": ["Medical Facility Inspector", "Fire Safety Certification"],
            "school": ["Child Safety Inspector", "Structural Integrity Certification"],
            "residential": ["General Inspector"],
            "factory": ["Industrial Systems Inspector", "Hazardous Materials Certification"],
        }
        compliance_map = {
            "fire_noncompliant": ["Fire Safety Certification"],
            "electrical_pending": ["Electrical Systems Certification"],
            "general_due": ["General Inspector"],
        }
    
        qualifications = []
        # Map by building type
        if building_type in qualification_map:
            qualifications += qualification_map[building_type]
        # Map by compliance status
        for key, qlist in compliance_map.items():
            if key in compliance_status:
                qualifications += qlist
        # Deduplicate and provide fallback
        if not qualifications:
            qualifications = ["General Inspector"]
        else:
            qualifications = list(set(qualifications))
    
        return { "success": True, "data": qualifications }

    def list_appointments_for_inspector(self, inspector_id: str) -> dict:
        """
        Retrieve all inspection appointments assigned to the specified inspector.

        Args:
            inspector_id (str): The unique identifier of the inspector.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[InspectionAppointmentInfo]  # May be empty if no appointments.
                }
                or
                {
                    "success": False,
                    "error": str  # Inspector does not exist
                }

        Constraints:
            - The inspector_id must exist in the inspector registry.
        """
        if inspector_id not in self.inspectors:
            return {"success": False, "error": "Inspector does not exist"}

        result = [
            appt for appt in self.appointments.values()
            if appt["inspector_id"] == inspector_id
        ]
        return {"success": True, "data": result}

    def list_appointments_for_building(self, building_id: str) -> dict:
        """
        Retrieve all inspection appointments scheduled for a specific building.

        Args:
            building_id (str): Unique identifier for the building.

        Returns:
            dict:
                On success:
                  {
                    "success": True,
                    "data": List[InspectionAppointmentInfo]  # List of all appointments for the building (may be empty).
                  }
                On failure (building not found):
                  {
                    "success": False,
                    "error": "Building not found"
                  }
        Constraints:
            - building_id must refer to an existing building.
        """
        if building_id not in self.buildings:
            return { "success": False, "error": "Building not found" }

        result = [
            appt for appt in self.appointments.values()
            if appt["building_id"] == building_id
        ]

        return { "success": True, "data": result }

    def get_appointments_by_datetime(
        self,
        inspector_id: Optional[str] = None,
        scheduled_date: Optional[str] = None
    ) -> dict:
        """
        Retrieve all inspection appointments, optionally filtering by inspector and/or scheduled date/time.

        Args:
            inspector_id (Optional[str]): If specified, only return appointments assigned to this inspector.
            scheduled_date (Optional[str]): If specified, only return appointments scheduled at this date/time (ISO datetime string).

        Returns:
            dict: {
                "success": True,
                "data": List[InspectionAppointmentInfo],  # All matching appointments (may be empty),
            }

        Notes:
            - If both filters are None, returns all appointments.
            - Filtering uses AND logic (i.e., both criteria must be met if both are provided).
        """
        results = []
        for appointment in self.appointments.values():
            if inspector_id is not None:
                if appointment['inspector_id'] != inspector_id:
                    continue
            if scheduled_date is not None:
                if appointment['scheduled_date'] != scheduled_date:
                    continue
            results.append(appointment)
        return {"success": True, "data": results}

    def get_appointment_by_id(self, appointment_id: str) -> dict:
        """
        Retrieve the details of a specific inspection appointment using its appointment_id.

        Args:
            appointment_id (str): The unique identifier for the inspection appointment.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": InspectionAppointmentInfo  # All details of the requested appointment
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Appointment not found"
                    }

        Constraints:
            - The appointment_id must exist in the system.
        """
        appointment = self.appointments.get(appointment_id)
        if not appointment:
            return { "success": False, "error": "Appointment not found" }
        return { "success": True, "data": appointment }

    def check_inspector_availability(self, inspector_id: str, scheduled_date: str) -> dict:
        """
        Determine if an inspector is available at a specific date and time slot.

        Args:
            inspector_id (str): The identifier of the inspector to check.
            scheduled_date (str): The date and time to check (ISO datetime string).

        Returns:
            dict: {
                "success": True,
                "available": bool  # True if available, False if not
            }
            or
            dict: {
                "success": False,
                "error": str  # Description of the error (e.g., inspector not found)
            }

        Constraints:
            - Inspector must exist.
            - Inspector cannot have another scheduled appointment at the same date/time.
        """

        if inspector_id not in self.inspectors:
            return { "success": False, "error": "Inspector not found" }

        # Scan all appointments for inspector and datetime matches, only where status is "scheduled"
        for appt in self.appointments.values():
            if (
                appt["inspector_id"] == inspector_id and
                appt["scheduled_date"] == scheduled_date and
                appt["status"].lower() == "scheduled"
            ):
                return { "success": True, "available": False }

        return { "success": True, "available": True }

    def get_appointment_status(self, appointment_id: str) -> dict:
        """
        Query the current status of a specific inspection appointment.

        Args:
            appointment_id (str): The unique identifier for the inspection appointment.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "status": str  # The current status of the appointment ("scheduled", "completed", "cancelled", etc.)
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason (e.g., appointment does not exist)
                    }
    
        Constraints:
            - The appointment_id must exist in the system.
        """
        appt = self.appointments.get(appointment_id)
        if not appt:
            return { "success": False, "error": "Appointment does not exist" }
        return { "success": True, "status": appt["status"] }

    def create_inspection_appointment(
        self,
        appointment_id: str,
        building_id: str,
        inspector_id: str,
        scheduled_date: str,
        results: Optional[str] = None,
        notes: Optional[str] = None
    ) -> dict:
        """
        Schedule a new inspection appointment for a specific building, inspector, and scheduled date, verifying all constraints.

        Args:
            appointment_id (str): Unique ID for the new appointment.
            building_id (str): ID of the building to inspect.
            inspector_id (str): ID of the inspector assigned.
            scheduled_date (str): ISO format string representing the inspection date/time.
            results (Optional[str]): Optional initial results field (default None).
            notes (Optional[str]): Optional notes about the appointment.

        Returns:
            dict: {
                "success": True,
                "message": "Appointment created for {building_id} with inspector {inspector_id} on {scheduled_date}"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - appointment_id must be unique.
            - building_id and inspector_id must exist.
            - inspector must not have another appointment at the same scheduled_date.
            - inspector must meet required qualifications for the building (if any).
        """
        # Check appointment_id is unique
        if appointment_id in self.appointments:
            return { "success": False, "error": "Appointment ID already exists" }
    
        # Check building exists
        building = self.buildings.get(building_id)
        if not building:
            return { "success": False, "error": "Building does not exist" }
    
        # Check inspector exists
        inspector = self.inspectors.get(inspector_id)
        if not inspector:
            return { "success": False, "error": "Inspector does not exist" }

        # Check inspector availability: not assigned to another appointment at same datetime
        for appt in self.appointments.values():
            if appt["inspector_id"] == inspector_id and appt["scheduled_date"] == scheduled_date and appt["status"] != "cancelled":
                return { "success": False, "error": "Inspector not available at the scheduled date/time" }
    
        # Qualification check (if implemented)
        required_qualifications = []
        if hasattr(self, "get_building_required_qualifications"):
            qres = self.get_building_required_qualifications(building_id)
            if qres.get("success"):
                required_qualifications = qres["data"] or []
            else:
                return { "success": False, "error": "Failed to retrieve building qualification requirements" }
        if required_qualifications:
            inspector_qualifications = inspector.get("qualifications") or []
            if not all(q in inspector_qualifications for q in required_qualifications):
                return { 
                    "success": False, 
                    "error": f"Inspector does not meet required qualifications: {required_qualifications}" 
                }

        # Prepare appointment info
        appointment: InspectionAppointmentInfo = {
            "appointment_id": appointment_id,
            "building_id": building_id,
            "inspector_id": inspector_id,
            "scheduled_date": scheduled_date,
            "status": "scheduled",
            "results": results,
            "notes": notes
        }

        self.appointments[appointment_id] = appointment

        return {
            "success": True,
            "message": f"Appointment created for {building_id} with inspector {inspector_id} on {scheduled_date}"
        }

    def update_appointment_status(self, appointment_id: str, new_status: str) -> dict:
        """
        Change the status of an inspection appointment.

        Args:
            appointment_id (str): The ID of the appointment to update.
            new_status (str): The new status string (e.g., 'scheduled', 'completed', 'cancelled').

        Returns:
            dict:
                On success: {"success": True, "message": "Appointment status updated."}
                On failure: {"success": False, "error": "<reason>"}

        Constraints:
            - The appointment_id must exist in the system.
            - new_status must be one of the allowed statuses.
            - Appointment status must actually change.
        """
        allowed_statuses = ["scheduled", "completed", "cancelled"]
        appointment = self.appointments.get(appointment_id)
        if not appointment:
            return {"success": False, "error": "Appointment not found."}
        if new_status not in allowed_statuses:
            return {"success": False, "error": f"Invalid status '{new_status}'."}
        if appointment["status"] == new_status:
            return {"success": False, "error": "Appointment already in the requested status."}

        appointment["status"] = new_status
        self.appointments[appointment_id] = appointment  # Not strictly necessary since it's mutable, but for clarity.

        return {"success": True, "message": "Appointment status updated."}

    def cancel_appointment(self, appointment_id: str) -> dict:
        """
        Cancel an existing scheduled appointment.

        Args:
            appointment_id (str): The ID of the appointment to cancel.

        Returns:
            dict: 
                - On success: {"success": True, "message": "Appointment <id> has been cancelled."}
                - On error: {"success": False, "error": "<reason>"}

        Constraints:
            - Appointment must exist.
            - Only appointments with status 'scheduled' can be cancelled.
            - Completed or already-cancelled appointments cannot be cancelled.
        """
        appointment = self.appointments.get(appointment_id)
        if not appointment:
            return {"success": False, "error": "Appointment not found."}

        if appointment["status"] == "cancelled":
            return {"success": False, "error": "Appointment is already cancelled."}

        if appointment["status"] == "completed":
            return {"success": False, "error": "Cannot cancel a completed appointment."}

        # Only allow cancellation if status is 'scheduled'
        if appointment["status"] != "scheduled":
            return {"success": False, "error": f"Appointment cannot be cancelled in its current state: {appointment['status']}"}

        appointment["status"] = "cancelled"
        return {"success": True, "message": f"Appointment {appointment_id} has been cancelled."}

    def modify_appointment_details(
        self,
        appointment_id: str,
        inspector_id: str = None,
        building_id: str = None,
        scheduled_date: str = None,
        results: str = None,
        notes: str = None
    ) -> dict:
        """
        Modify attributes of an inspection appointment. Supports changing inspector, building, date/time, results, or notes.

        Args:
            appointment_id (str): Appointment to modify.
            inspector_id (str, optional): New inspector assignment.
            building_id (str, optional): New building assignment.
            scheduled_date (str, optional): New scheduled time (ISO datetime string).
            results (str, optional): Results of the inspection.
            notes (str, optional): Additional notes.

        Returns:
            dict: {
                "success": True,
                "message": "Appointment details modified successfully",
            }
            or
            {
                "success": False,
                "error": <description>
            }

        Constraints:
            - The appointment, building, and inspector must exist if referenced.
            - No inspector may be double-booked at a single time.
            - Inspector must be qualified for the assigned building.
        """
        if appointment_id not in self.appointments:
            return { "success": False, "error": "Appointment does not exist" }
        if not any([inspector_id, building_id, scheduled_date, results, notes]):
            return { "success": False, "error": "No fields to modify" }

        app = self.appointments[appointment_id]
        # Prepare new values to validate atomically
        new_building_id = building_id if building_id is not None else app['building_id']
        new_inspector_id = inspector_id if inspector_id is not None else app['inspector_id']
        new_scheduled_date = scheduled_date if scheduled_date is not None else app['scheduled_date']

        # 1. Validate building
        if new_building_id not in self.buildings:
            return { "success": False, "error": "Building does not exist" }

        # 2. Validate inspector
        if new_inspector_id not in self.inspectors:
            return { "success": False, "error": "Inspector does not exist" }

        # 3. Check inspector's qualifications for building
        building = self.buildings[new_building_id]
        inspector = self.inspectors[new_inspector_id]
        # Helper: Get building's required qualifications
        required_quals = set()
        if hasattr(self, 'get_building_required_qualifications'):
            q_res = self.get_building_required_qualifications(new_building_id)
            if q_res["success"]:
                required_quals = set(q_res["data"])  # assume it's a list
        if required_quals and not required_quals.issubset(set(inspector['qualifications'])):
            return { "success": False, "error": "Inspector does not have required qualifications for this building" }

        # 4. Check inspector double-booking on new_scheduled_date (exclude this appointment)
        for other_app in self.appointments.values():
            if (
                other_app['appointment_id'] != appointment_id and
                other_app['inspector_id'] == new_inspector_id and
                other_app['scheduled_date'] == new_scheduled_date and
                other_app['status'] not in ['cancelled']
            ):
                return { "success": False, "error": "Inspector is already assigned to another appointment at this date/time" }

        # All checks passed, apply changes atomically
        if inspector_id is not None:
            app["inspector_id"] = inspector_id
        if building_id is not None:
            app["building_id"] = building_id
        if scheduled_date is not None:
            app["scheduled_date"] = scheduled_date
        if results is not None:
            app["results"] = results
        if notes is not None:
            app["notes"] = notes

        return { "success": True, "message": "Appointment details modified successfully" }

    def delete_appointment(self, appointment_id: str) -> dict:
        """
        Permanently removes an inspection appointment from the system.

        Args:
            appointment_id (str): The unique ID of the appointment to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Appointment <appointment_id> has been deleted."
            }
            or
            {
                "success": False,
                "error": "Appointment not found."
            }

        Constraints:
            - Only existing appointments can be deleted.
        """
        if appointment_id not in self.appointments:
            return {"success": False, "error": "Appointment not found."}

        del self.appointments[appointment_id]
        return {"success": True, "message": f"Appointment {appointment_id} has been deleted."}

    def record_appointment_results(
        self,
        appointment_id: str,
        results: str,
        notes: Optional[str] = None
    ) -> dict:
        """
        Store results and notes after an inspection is completed.

        Args:
            appointment_id (str): The unique ID of the inspection appointment.
            results (str): Summary/results of the inspection.
            notes (Optional[str]): Additional notes (optional).

        Returns:
            dict:
                - { "success": True, "message": "Results and notes recorded for appointment <appointment_id>." }
                - { "success": False, "error": "<reason>" }
        Constraints:
            - Appointment must exist.
            - Appointment status must be 'completed' to record results.
        """
        appointment = self.appointments.get(appointment_id)
        if not appointment:
            return { "success": False, "error": "Appointment does not exist" }

        if appointment["status"] != "completed":
            return { "success": False, "error": "Can only record results for completed inspections" }

        appointment["results"] = results
        appointment["notes"] = notes

        return {
            "success": True,
            "message": f"Results and notes recorded for appointment {appointment_id}."
        }

    def assign_inspector_to_appointment(self, appointment_id: str, inspector_id: str) -> dict:
        """
        Assign or change an inspector for an existing appointment, enforcing all eligibility and availability constraints.

        Args:
            appointment_id (str): Unique identifier of the inspection appointment.
            inspector_id (str): Unique identifier of the inspector to assign.

        Returns:
            dict: {
                "success": True,
                "message": str  # Success message
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - Both appointment and inspector must exist.
            - Appointment must be in a modifiable status (not completed or canceled).
            - Inspector cannot already be assigned to another appointment at the same scheduled_date.
            - Inspector must possess all needed qualifications for the building/appointment.
        """
        appt = self.appointments.get(appointment_id)
        if not appt:
            return {"success": False, "error": "Appointment does not exist."}

        inspector = self.inspectors.get(inspector_id)
        if not inspector:
            return {"success": False, "error": "Inspector does not exist."}

        # Only allow assignment if appointment is scheduled (not completed/canceled)
        if appt['status'] not in ('scheduled',):
            return {"success": False, "error": f"Cannot assign inspector; appointment status is '{appt['status']}'."}

        # Prevent double-booking inspector for the same datetime
        scheduled_date = appt['scheduled_date']
        for other in self.appointments.values():
            if (
                other['appointment_id'] != appointment_id
                and other['inspector_id'] == inspector_id
                and other['scheduled_date'] == scheduled_date
                and other['status'] == 'scheduled'
            ):
                return {"success": False, "error": "Inspector is already assigned to another inspection at the same date and time."}

        # Qualification check: the building might require certain qualifications
        building = self.buildings.get(appt['building_id'])
        if not building:
            return {"success": False, "error": "Associated building does not exist."}
        # Assume get_building_required_qualifications exists and returns List[str]
        if hasattr(self, 'get_building_required_qualifications'):
            result = self.get_building_required_qualifications(appt['building_id'])
            if result.get('success'):
                required_quals = result['data']
                if not set(required_quals).issubset(set(inspector['qualifications'])):
                    return {"success": False, "error": "Inspector does not meet required qualifications for this building."}

        # Assign inspector
        appt['inspector_id'] = inspector_id

        return {
            "success": True,
            "message": f"Inspector {inspector_id} assigned to appointment {appointment_id}."
        }


class BuildingInspectionSchedulingSystem(BaseEnv):
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
            copied = copy.deepcopy(value)
            if key == "get_building_required_qualifications":
                setattr(env, "_qualification_rules_text", copied)
                continue
            setattr(env, key, copied)

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

    def get_building_by_id(self, **kwargs):
        return self._call_inner_tool('get_building_by_id', kwargs)

    def list_all_buildings(self, **kwargs):
        return self._call_inner_tool('list_all_buildings', kwargs)

    def get_inspector_by_id(self, **kwargs):
        return self._call_inner_tool('get_inspector_by_id', kwargs)

    def list_all_inspectors(self, **kwargs):
        return self._call_inner_tool('list_all_inspectors', kwargs)

    def check_inspector_qualifications(self, **kwargs):
        return self._call_inner_tool('check_inspector_qualifications', kwargs)

    def get_building_required_qualifications(self, **kwargs):
        return self._call_inner_tool('get_building_required_qualifications', kwargs)

    def list_appointments_for_inspector(self, **kwargs):
        return self._call_inner_tool('list_appointments_for_inspector', kwargs)

    def list_appointments_for_building(self, **kwargs):
        return self._call_inner_tool('list_appointments_for_building', kwargs)

    def get_appointments_by_datetime(self, **kwargs):
        return self._call_inner_tool('get_appointments_by_datetime', kwargs)

    def get_appointment_by_id(self, **kwargs):
        return self._call_inner_tool('get_appointment_by_id', kwargs)

    def check_inspector_availability(self, **kwargs):
        return self._call_inner_tool('check_inspector_availability', kwargs)

    def get_appointment_status(self, **kwargs):
        return self._call_inner_tool('get_appointment_status', kwargs)

    def create_inspection_appointment(self, **kwargs):
        return self._call_inner_tool('create_inspection_appointment', kwargs)

    def update_appointment_status(self, **kwargs):
        return self._call_inner_tool('update_appointment_status', kwargs)

    def cancel_appointment(self, **kwargs):
        return self._call_inner_tool('cancel_appointment', kwargs)

    def modify_appointment_details(self, **kwargs):
        return self._call_inner_tool('modify_appointment_details', kwargs)

    def delete_appointment(self, **kwargs):
        return self._call_inner_tool('delete_appointment', kwargs)

    def record_appointment_results(self, **kwargs):
        return self._call_inner_tool('record_appointment_results', kwargs)

    def assign_inspector_to_appointment(self, **kwargs):
        return self._call_inner_tool('assign_inspector_to_appointment', kwargs)
