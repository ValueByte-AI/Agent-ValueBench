# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
import uuid
from typing import Optional
import hashlib



class PatientInfo(TypedDict):
    patient_id: str
    name: str
    DOB: str
    contact_info: str
    medical_history: str

class HospitalInfo(TypedDict):
    hospital_id: str
    name: str
    location: str
    available_resources: str

class ProcedureInfo(TypedDict):
    procedure_id: str
    name: str
    category: str
    typical_duration: float

class SurgeryWaitlistEntryInfo(TypedDict):
    entry_id: str
    hospital_id: str
    patient_id: str
    procedure_id: str
    timestamp: str
    status: str

class ScheduledSurgeryInfo(TypedDict):
    surgery_id: str
    hospital_id: str
    patient_id: str
    procedure_id: str
    scheduled_time: str
    assigned_resources: str
    status: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Hospital surgery scheduling system environment.
        Entities: patients, hospitals, procedures, surgery waitlist entries, scheduled surgeries.
        """

        # Patients: {patient_id: PatientInfo}
        self.patients: Dict[str, PatientInfo] = {}

        # Hospitals: {hospital_id: HospitalInfo}
        self.hospitals: Dict[str, HospitalInfo] = {}

        # Procedures: {procedure_id: ProcedureInfo}
        self.procedures: Dict[str, ProcedureInfo] = {}

        # Surgery waitlist entries: {entry_id: SurgeryWaitlistEntryInfo}
        self.surgery_waitlist: Dict[str, SurgeryWaitlistEntryInfo] = {}

        # Scheduled surgeries: {surgery_id: ScheduledSurgeryInfo}
        self.scheduled_surgeries: Dict[str, ScheduledSurgeryInfo] = {}

        # Optional per-hospital reusable resource block configurations.
        # Example:
        # {"H1": {"General-Surgical-Team": {"scheduled_time": "tomorrow 08:00", "capacity_hours": 9.0}}}
        self.resource_block_capacity_hours: Dict[str, Dict[str, float]] = {}

        # Constraints:
        # - A patient can only be on the waitlist for a specific procedure in a given hospital once at a time.
        # - No waitlist entry can exist for nonexistent hospital, patient, or procedure.
        # - Waitlist entries must be processed in order of priority (usually by timestamp and/or medical urgency).
        # - Only available hospital resources can be allocated to scheduled surgeries.

    def _get_resource_block_config(self, hospital_id: str, assigned_resources: str):
        hospital_caps = self.resource_block_capacity_hours.get(hospital_id, {})
        if not isinstance(hospital_caps, dict):
            return None
        raw = hospital_caps.get(assigned_resources)
        if raw is None:
            return None
        if isinstance(raw, dict):
            try:
                capacity_hours = float(raw.get("capacity_hours"))
            except (TypeError, ValueError):
                return None
            scheduled_time = raw.get("scheduled_time")
            if scheduled_time is not None and not isinstance(scheduled_time, str):
                return None
            return {
                "capacity_hours": capacity_hours,
                "scheduled_time": scheduled_time,
            }
        try:
            return {
                "capacity_hours": float(raw),
                "scheduled_time": None,
            }
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _get_service_day_key(raw_time: Optional[str]) -> Optional[str]:
        if not isinstance(raw_time, str):
            return None
        normalized = raw_time.strip()
        if not normalized:
            return None

        lowered = normalized.lower()
        for relative_day in ("today", "tomorrow", "yesterday"):
            if lowered.startswith(relative_day):
                return relative_day

        if "T" in normalized and len(normalized) >= 10 and normalized[:10].count("-") == 2:
            return normalized[:10]

        first_token = normalized.split()[0]
        if len(first_token) == 10 and first_token.count("-") == 2:
            return first_token

        return None

    def _get_used_resource_block_hours(
        self,
        hospital_id: str,
        assigned_resources: str,
        service_day_key: Optional[str] = None,
        exact_scheduled_time: Optional[str] = None,
    ) -> float:
        used = 0.0
        for surgery in self.scheduled_surgeries.values():
            if surgery.get("hospital_id") != hospital_id:
                continue
            if surgery.get("assigned_resources") != assigned_resources:
                continue

            surgery_time = surgery.get("scheduled_time")
            if service_day_key is not None:
                if self._get_service_day_key(surgery_time) != service_day_key:
                    continue
            elif exact_scheduled_time is not None and surgery_time != exact_scheduled_time:
                continue

            procedure = self.procedures.get(surgery.get("procedure_id"))
            if procedure is None:
                continue
            try:
                used += float(procedure.get("typical_duration", 0.0))
            except (TypeError, ValueError):
                continue
        return used

    def get_patient_by_name(self, name: str) -> dict:
        """
        Retrieve information for all patients with the given name.

        Args:
            name (str): The patient's name to search for.

        Returns:
            dict: {
                "success": True,
                "data": List[PatientInfo]  # All matching patients (may be empty if none)
            }
            or
            {
                "success": False,
                "error": str  # No patient found with the given name
            }

        Notes:
            - Patient names are not guaranteed unique; returns all exact matches.
            - If no patient found, returns an error.
        """
        matches = [info for info in self.patients.values() if info["name"] == name]
        if not matches:
            return {"success": False, "error": "No patient found with the given name."}
        return {"success": True, "data": matches}

    def get_patient_by_id(self, patient_id: str) -> dict:
        """
        Retrieve a patient's information by patient_id.

        Args:
            patient_id (str): Unique identifier of the patient.

        Returns:
            dict: {
                "success": True,
                "data": PatientInfo  # On successful retrieval
            }
            or
            {
                "success": False,
                "error": str  # If the patient_id does not exist
            }

        Constraints:
            - patient_id must exist within self.patients.
        """
        patient = self.patients.get(patient_id)
        if not patient:
            return { "success": False, "error": "Patient not found" }
        return { "success": True, "data": patient }

    def list_all_patients(self) -> dict:
        """
        Return a list of all registered patients.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[PatientInfo]  # May be empty if no patients are registered.
            }
        Constraints:
            None.
        """
        all_patients = list(self.patients.values())
        return { "success": True, "data": all_patients }

    def get_hospital_by_id(self, hospital_id: str) -> dict:
        """
        Fetch the details for a hospital (name, location, available resources) with the given hospital_id.

        Args:
            hospital_id (str): Unique identifier for the hospital.

        Returns:
            dict: {
                "success": True,
                "data": HospitalInfo  # keys: hospital_id, name, location, available_resources
            }
            or
            {
                "success": False,
                "error": str  # Description if hospital_id not found.
            }

        Constraints:
            - The hospital must exist in the system.
        """
        if hospital_id not in self.hospitals:
            return {"success": False, "error": "Hospital does not exist"}

        return {"success": True, "data": self.hospitals[hospital_id]}

    def list_all_hospitals(self) -> dict:
        """
        List all hospitals registered in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[HospitalInfo]  # List of hospital info dicts; may be empty if system has no hospitals
            }
        """
        hospitals = list(self.hospitals.values())
        return {"success": True, "data": hospitals}

    def get_procedure_by_name(self, name: str) -> dict:
        """
        Retrieve procedure info given its name.

        Args:
            name (str): The name of the procedure to search for (case-sensitive).

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": ProcedureInfo
                    }
                - On failure:
                    {
                        "success": False,
                        "error": "Procedure not found"
                    }
        Constraints:
            - If there is no procedure with the given name, return error.
            - Name matching is case-sensitive.
        """
        for proc in self.procedures.values():
            if proc["name"] == name:
                return { "success": True, "data": proc }
        return { "success": False, "error": "Procedure not found" }

    def list_hospital_procedures(self, hospital_id: str) -> dict:
        """
        List all procedures available at a given hospital.

        Args:
            hospital_id (str): The unique identifier for the hospital.

        Returns:
            dict: {
                "success": True,
                "data": List[ProcedureInfo],  # All procedures (may be empty if none present)
            }
            or
            {
                "success": False,
                "error": str  # e.g., hospital does not exist
            }

        Constraints:
            - The hospital must exist.
            - If no procedures are present, returns empty list.
            - Assumes all procedures are available at all hospitals in this implementation.
        """
        if hospital_id not in self.hospitals:
            return {"success": False, "error": "Hospital does not exist"}

        procedure_list = list(self.procedures.values())
        return {"success": True, "data": procedure_list}

    def get_waitlist_entry(self, hospital_id: str, patient_id: str, procedure_id: str) -> dict:
        """
        Retrieve the waitlist entry for a given patient, hospital, and procedure combination
        (used to check uniqueness constraint before adding a new entry).

        Args:
            hospital_id (str): ID of the hospital.
            patient_id (str): ID of the patient.
            procedure_id (str): ID of the surgical procedure.

        Returns:
            dict: { 
                "success": True,
                "data": SurgeryWaitlistEntryInfo or None  # The matching entry, or None if not found
            }
        Constraints:
            - Does not error if entities don't exist, just checks for a matching combination in waitlist.
            - At most one entry should exist per the system’s constraints.
        """

        entry = None
        for waitlist_entry in self.surgery_waitlist.values():
            if (waitlist_entry["hospital_id"] == hospital_id and
                waitlist_entry["patient_id"] == patient_id and
                waitlist_entry["procedure_id"] == procedure_id):
                entry = waitlist_entry
                break

        return {
            "success": True,
            "data": entry
        }

    def list_waitlist_for_hospital(self, hospital_id: str) -> dict:
        """
        List all waitlist entries for the specified hospital.

        Args:
            hospital_id (str): The ID of the hospital.

        Returns:
            dict: {
                "success": True,
                "data": List[SurgeryWaitlistEntryInfo]  # May be empty if no entries
            }
            or
            {
                "success": False,
                "error": str  # If the hospital does not exist
            }

        Constraints:
            - Hospital must exist.
            - Only entries belonging to given hospital_id are included.
        """
        if hospital_id not in self.hospitals:
            return { "success": False, "error": "Hospital does not exist" }

        entries = [
            entry for entry in self.surgery_waitlist.values()
            if entry["hospital_id"] == hospital_id
        ]

        return { "success": True, "data": entries }

    def list_waitlist_for_procedure(self, hospital_id: str, procedure_id: str) -> dict:
        """
        List all surgery waitlist entries for a given procedure at a specified hospital.

        Args:
            hospital_id (str): The ID of the hospital.
            procedure_id (str): The ID of the surgical procedure.

        Returns:
            dict: {
                "success": True,
                "data": List[SurgeryWaitlistEntryInfo]
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Returns only entries where both the hospital and procedure exist.
            - Returns an empty list if no entries are found for the given criteria.
        """
        if not hospital_id or hospital_id not in self.hospitals:
            return {"success": False, "error": "Hospital does not exist"}

        if not procedure_id or procedure_id not in self.procedures:
            return {"success": False, "error": "Procedure does not exist"}

        results = [
            entry for entry in self.surgery_waitlist.values()
            if entry["hospital_id"] == hospital_id and entry["procedure_id"] == procedure_id
        ]

        return {"success": True, "data": results}

    def check_resource_availability(self, hospital_id: str) -> dict:
        """
        Query the available resources at a specified hospital.

        Args:
            hospital_id (str): The unique identifier for the hospital to query.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": str  # Available resources information
                }
            or
                {
                    "success": False,
                    "error": str  # Description of error (e.g., hospital does not exist)
                }

        Constraints:
            - The hospital with the given hospital_id must exist.
        """
        hospital = self.hospitals.get(hospital_id)
        if hospital is None:
            return { "success": False, "error": "Hospital does not exist" }
        return { "success": True, "data": hospital["available_resources"] }


    def add_waitlist_entry(
        self, 
        patient_id: str, 
        hospital_id: str, 
        procedure_id: str, 
        timestamp: str, 
        status: Optional[str] = "waiting"
    ) -> dict:
        """
        Add a new entry to the surgery waitlist for a patient/procedure/hospital, subject to constraints:
          - Patient, hospital, and procedure must exist.
          - Patient cannot already be on the waitlist for the same procedure and hospital at the same time (unless status is 'removed').
          - New entry receives a unique entry_id.

        Args:
            patient_id (str): The ID of the patient to be added to the waitlist.
            hospital_id (str): The hospital in which the procedure is requested.
            procedure_id (str): The surgical procedure being requested.
            timestamp (str): The timestamp of request (e.g., ISO format).
            status (str, optional): Initial waitlist status. Default is 'waiting'.

        Returns:
            dict: {
              "success": True, 
              "message": "Waitlist entry added", 
              "entry_id": <entry_id>
            }
            Or {
              "success": False,
              "error": <reason>
            }
        """
        # Existence checks
        if patient_id not in self.patients:
            return {"success": False, "error": "Patient does not exist"}
        if hospital_id not in self.hospitals:
            return {"success": False, "error": "Hospital does not exist"}
        if procedure_id not in self.procedures:
            return {"success": False, "error": "Procedure does not exist"}
    
        # Uniqueness constraint: Only one entry per patient/procedure/hospital
        for entry in self.surgery_waitlist.values():
            if (
                entry["patient_id"] == patient_id and
                entry["hospital_id"] == hospital_id and
                entry["procedure_id"] == procedure_id and
                entry["status"] != "removed"  # Only allow if existing is 'removed'
            ):
                return {"success": False, "error": "Patient is already on the waitlist for this procedure at this hospital"}
    
        # Generate unique entry_id
        entry_id = str(uuid.uuid4())
        # Build the entry
        entry: SurgeryWaitlistEntryInfo = {
            "entry_id": entry_id,
            "hospital_id": hospital_id,
            "patient_id": patient_id,
            "procedure_id": procedure_id,
            "timestamp": timestamp,
            "status": status
        }
        self.surgery_waitlist[entry_id] = entry
        return {"success": True, "message": "Waitlist entry added", "entry_id": entry_id}

    def update_waitlist_entry_status(self, entry_id: str, new_status: str) -> dict:
        """
        Change the status of a waitlist entry (e.g., from waiting to scheduled or removed).

        Args:
            entry_id (str): The unique identifier of the waitlist entry.
            new_status (str): The new status to set (e.g., "waiting", "scheduled", "removed").

        Returns:
            dict: {
                "success": True,
                "message": "Waitlist entry status updated to <new_status>"
            }
            or
            {
                "success": False,
                "error": str  # Description of the error
            }

        Constraints:
            - The waitlist entry must exist.
        """
        if entry_id not in self.surgery_waitlist:
            return { "success": False, "error": "Waitlist entry does not exist" }

        self.surgery_waitlist[entry_id]["status"] = new_status

        return {
            "success": True,
            "message": f"Waitlist entry status updated to {new_status}"
        }

    def remove_waitlist_entry(self, entry_id: str) -> dict:
        """
        Remove an entry from the surgery waitlist using its entry_id.

        Args:
            entry_id (str): Unique identifier of the waitlist entry.

        Returns:
            dict:
                - On success: { "success": True, "message": "Waitlist entry removed." }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - Entry must exist in the current surgery waitlist to be removed.
        """
        if entry_id not in self.surgery_waitlist:
            return { "success": False, "error": "Waitlist entry does not exist." }
        del self.surgery_waitlist[entry_id]
        return { "success": True, "message": "Waitlist entry removed." }

    def schedule_surgery(
        self,
        entry_id: str,
        scheduled_time: str,
        assigned_resources: str
    ) -> dict:
        """
        Move an eligible waitlist entry into a scheduled surgery, allocating hospital resources.

        Args:
            entry_id (str): ID of the waitlist entry to promote to scheduled surgery.
            scheduled_time (str): When the surgery is to be scheduled.
            assigned_resources (str): Resources (as a string) to allocate from the hospital.

        Returns:
            dict:
                On success: {
                    "success": True,
                    "message": "Surgery scheduled for patient X at hospital Y for procedure Z."
                }
                On failure: {
                    "success": False,
                    "error": "reason"
                }

        Constraints:
            - Waitlist entry must exist and be in eligible status (e.g., 'waiting').
            - Referenced hospital, patient, and procedure must exist.
            - Only available hospital resources can be allocated to scheduled surgeries.
            - On success, the status of the waitlist entry is updated to 'scheduled'.
        """

        # 1. Check waitlist entry exists
        entry = self.surgery_waitlist.get(entry_id)
        if not entry:
            return {"success": False, "error": "Waitlist entry does not exist."}
    
        # 2. Check status
        if entry['status'] != 'waiting':
            return {"success": False, "error": f"Waitlist entry status is '{entry['status']}', not eligible for scheduling."}
    
        hospital_id = entry['hospital_id']
        patient_id = entry['patient_id']
        procedure_id = entry['procedure_id']

        # 3. Check referenced entities exist
        if hospital_id not in self.hospitals:
            return {"success": False, "error": "Hospital does not exist."}
        if patient_id not in self.patients:
            return {"success": False, "error": "Patient does not exist."}
        if procedure_id not in self.procedures:
            return {"success": False, "error": "Procedure does not exist."}

        hospital = self.hospitals[hospital_id]

        # 4. Check assigned resources are available
        # For illustrative purposes we check exact string match, but for a real implementation,
        # assigned_resources should be a structured type and the check must be stricter.
        if assigned_resources not in hospital["available_resources"]:
            return {"success": False, "error": "Requested resources are not available in the hospital."}

        block_config = self._get_resource_block_config(hospital_id, assigned_resources)
        if block_config is not None:
            allowed_block_time = block_config.get("scheduled_time")
            allowed_day_key = self._get_service_day_key(allowed_block_time)
            requested_day_key = self._get_service_day_key(scheduled_time)
            if allowed_block_time is not None:
                if allowed_day_key is not None and requested_day_key is not None:
                    if allowed_day_key != requested_day_key:
                        return {"success": False, "error": "Requested resources are not available in the hospital."}
                elif scheduled_time != allowed_block_time:
                    return {"success": False, "error": "Requested resources are not available in the hospital."}
            try:
                requested_duration = float(self.procedures[procedure_id].get("typical_duration", 0.0))
            except (TypeError, ValueError):
                requested_duration = 0.0
            used_hours = self._get_used_resource_block_hours(
                hospital_id,
                assigned_resources,
                service_day_key=allowed_day_key or requested_day_key,
                exact_scheduled_time=allowed_block_time if (allowed_day_key is None and requested_day_key is None) else None,
            )
            if used_hours + requested_duration > block_config["capacity_hours"]:
                return {
                    "success": False,
                    "error": "Requested resource block capacity exceeded for the scheduled time."
                }

        # 5. Generate a unique surgery_id (using entry_id and scheduled_time for simplicity)
        surgery_id_input = entry_id + scheduled_time
        surgery_id = hashlib.md5(surgery_id_input.encode('utf-8')).hexdigest()

        # 6. Create scheduled surgery entry
        scheduled_surgery: ScheduledSurgeryInfo = {
            "surgery_id": surgery_id,
            "hospital_id": hospital_id,
            "patient_id": patient_id,
            "procedure_id": procedure_id,
            "scheduled_time": scheduled_time,
            "assigned_resources": assigned_resources,
            "status": "scheduled"
        }
        self.scheduled_surgeries[surgery_id] = scheduled_surgery

        # 7. Update waitlist entry status
        self.surgery_waitlist[entry_id]['status'] = 'scheduled'

        # 8. Remove assigned_resources from hospital's available resources string (demo purpose),
        # unless this resource is explicitly configured as a reusable time block.
        if block_config is None:
            updated_resources = hospital["available_resources"].replace(assigned_resources, "")
            updated_resources = ", ".join(
                part.strip() for part in updated_resources.split(",") if part.strip()
            )
            hospital["available_resources"] = updated_resources

        patient_name = self.patients[patient_id]['name']
        hospital_name = self.hospitals[hospital_id]['name']
        procedure_name = self.procedures[procedure_id]['name']

        return {
            "success": True,
            "message": f"Surgery scheduled for patient {patient_name} at hospital {hospital_name} for procedure {procedure_name}."
        }

    def update_hospital_resources(self, hospital_id: str, new_available_resources: str) -> dict:
        """
        Adjust hospital available resources (e.g., after surgery is scheduled or resources are freed).

        Args:
            hospital_id (str): The unique identifier for the hospital whose resources are to be updated.
            new_available_resources (str): The new descriptor for available resources.

        Returns:
            dict: {
                "success": True,
                "message": "Hospital resources updated"
            }
            or
            {
                "success": False,
                "error": "Hospital not found"
            }

        Constraints:
            - The hospital_id must correspond to an existing hospital.
            - new_available_resources is treated as a string per HospitalInfo definition.
        """
        if hospital_id not in self.hospitals:
            return {"success": False, "error": "Hospital not found"}

        self.hospitals[hospital_id]["available_resources"] = new_available_resources
        return {"success": True, "message": "Hospital resources updated"}

    def update_patient_info(
        self, 
        patient_id: str, 
        name: str = None, 
        DOB: str = None, 
        contact_info: str = None, 
        medical_history: str = None
    ) -> dict:
        """
        Modify patient records fields (name, DOB, contact_info, medical_history) for a given patient.

        Args:
            patient_id (str): The unique patient identifier to update.
            name (str, optional): New name for the patient.
            DOB (str, optional): New date of birth.
            contact_info (str, optional): New contact information.
            medical_history (str, optional): New medical history summary or notes.

        Returns:
            dict: 
                On success: { "success": True, "message": "Patient info updated." }
                On failure: { "success": False, "error": "<description>" }

        Constraints:
            - patient_id must exist in the environment's patient records.
            - Only updates fields provided (and recognized).
            - patient_id cannot be changed by this method.
        """
        if patient_id not in self.patients:
            return { "success": False, "error": "Patient with given ID does not exist." }

        update_fields = {
            "name": name,
            "DOB": DOB,
            "contact_info": contact_info,
            "medical_history": medical_history
        }
        updated = False
        for k, v in update_fields.items():
            if v is not None:
                self.patients[patient_id][k] = v
                updated = True

        if not updated:
            return { "success": False, "error": "No valid fields supplied for update." }

        return { "success": True, "message": "Patient info updated." }

    def update_procedure_info(
        self,
        procedure_id: str,
        name: str = None,
        category: str = None,
        typical_duration: float = None
    ) -> dict:
        """
        Modify mutable fields of a surgery/procedure.
    
        Args:
            procedure_id (str): ID of the procedure to be updated.
            name (str, optional): New name for the procedure.
            category (str, optional): New category.
            typical_duration (float, optional): New typical duration (hours).

        Returns:
            dict:
                On success: {"success": True, "message": "Procedure info updated"}
                On failure: {"success": False, "error": "<reason>"}
    
        Constraints:
            - procedure_id must exist in the system.
            - typical_duration must be positive if provided.
            - At least one updatable field must be given.
        """
        if procedure_id not in self.procedures:
            return {"success": False, "error": "Procedure does not exist"}

        if name is None and category is None and typical_duration is None:
            return {"success": False, "error": "No update fields provided"}

        procedure = self.procedures[procedure_id]
        updated = False

        if name is not None:
            procedure['name'] = name
            updated = True

        if category is not None:
            procedure['category'] = category
            updated = True

        if typical_duration is not None:
            if not isinstance(typical_duration, (int, float)) or typical_duration <= 0:
                return {"success": False, "error": "typical_duration must be positive number"}
            procedure['typical_duration'] = typical_duration
            updated = True

        if not updated:
            return {"success": False, "error": "No valid fields to update"}

        # Save back (not strictly necessary for mutable dicts, but for clarity)
        self.procedures[procedure_id] = procedure

        return {"success": True, "message": "Procedure info updated"}

    def update_surgery_status(self, surgery_id: str, new_status: str) -> dict:
        """
        Change the status of a scheduled surgery.

        Args:
            surgery_id (str): The unique identifier for the scheduled surgery.
            new_status (str): The new status to assign (e.g., "completed", "cancelled", "rescheduled").

        Returns:
            dict: {
                "success": True,
                "message": "Surgery status updated to <new_status>."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }
    
        Constraints:
            - The surgery_id must exist in the scheduled surgeries.
            - No other scheduling rules restrict direct status update.
        """
        if not surgery_id or not new_status:
            return { "success": False, "error": "Missing surgery_id or new_status." }
    
        surgery = self.scheduled_surgeries.get(surgery_id)
        if not surgery:
            return { "success": False, "error": "Scheduled surgery not found." }
    
        surgery['status'] = new_status
        self.scheduled_surgeries[surgery_id] = surgery  # For clarity, but dict is mutable.

        return {
            "success": True,
            "message": f"Surgery status updated to {new_status}."
        }


class HospitalSurgerySchedulingSystem(BaseEnv):
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

    def get_patient_by_name(self, **kwargs):
        return self._call_inner_tool('get_patient_by_name', kwargs)

    def get_patient_by_id(self, **kwargs):
        return self._call_inner_tool('get_patient_by_id', kwargs)

    def list_all_patients(self, **kwargs):
        return self._call_inner_tool('list_all_patients', kwargs)

    def get_hospital_by_id(self, **kwargs):
        return self._call_inner_tool('get_hospital_by_id', kwargs)

    def list_all_hospitals(self, **kwargs):
        return self._call_inner_tool('list_all_hospitals', kwargs)

    def get_procedure_by_name(self, **kwargs):
        return self._call_inner_tool('get_procedure_by_name', kwargs)

    def list_hospital_procedures(self, **kwargs):
        return self._call_inner_tool('list_hospital_procedures', kwargs)

    def get_waitlist_entry(self, **kwargs):
        return self._call_inner_tool('get_waitlist_entry', kwargs)

    def list_waitlist_for_hospital(self, **kwargs):
        return self._call_inner_tool('list_waitlist_for_hospital', kwargs)

    def list_waitlist_for_procedure(self, **kwargs):
        return self._call_inner_tool('list_waitlist_for_procedure', kwargs)

    def check_resource_availability(self, **kwargs):
        return self._call_inner_tool('check_resource_availability', kwargs)

    def add_waitlist_entry(self, **kwargs):
        return self._call_inner_tool('add_waitlist_entry', kwargs)

    def update_waitlist_entry_status(self, **kwargs):
        return self._call_inner_tool('update_waitlist_entry_status', kwargs)

    def remove_waitlist_entry(self, **kwargs):
        return self._call_inner_tool('remove_waitlist_entry', kwargs)

    def schedule_surgery(self, **kwargs):
        return self._call_inner_tool('schedule_surgery', kwargs)

    def update_hospital_resources(self, **kwargs):
        return self._call_inner_tool('update_hospital_resources', kwargs)

    def update_patient_info(self, **kwargs):
        return self._call_inner_tool('update_patient_info', kwargs)

    def update_procedure_info(self, **kwargs):
        return self._call_inner_tool('update_procedure_info', kwargs)

    def update_surgery_status(self, **kwargs):
        return self._call_inner_tool('update_surgery_status', kwargs)
