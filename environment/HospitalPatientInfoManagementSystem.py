# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
from datetime import datetime
import uuid



# Patient: patient_id, name, birth_date, gender, hometown, address, contact_info, medical_history_reference, current_admission_reference
class PatientInfo(TypedDict):
    patient_id: str
    name: str
    birth_date: str
    gender: str
    hometown: str
    address: str
    contact_info: str
    medical_history_reference: str
    current_admission_reference: str

# Admission: admission_id, patient_id, admission_date, discharge_date, room_number, attending_physician_id, status
class AdmissionInfo(TypedDict):
    admission_id: str
    patient_id: str
    admission_date: str
    discharge_date: str
    room_number: str
    attending_physician_id: str
    status: str

# MedicalHistory: history_id, patient_id, diagnoses, allergies, medications, procedures, notes
class MedicalHistoryInfo(TypedDict):
    history_id: str
    patient_id: str
    diagnoses: List[str]
    allergies: List[str]
    medications: List[str]
    procedures: List[str]
    notes: str

# Staff: staff_id, name, role, department, access_level
class StaffInfo(TypedDict):
    staff_id: str
    name: str
    role: str
    department: str
    access_level: str

# RoleDefinition: role_name, permissions, description
class RoleDefinitionInfo(TypedDict):
    role_name: str
    permissions: List[str]
    description: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Patients: {patient_id: PatientInfo}
        self.patients: Dict[str, PatientInfo] = {}

        # Admissions: {admission_id: AdmissionInfo}
        self.admissions: Dict[str, AdmissionInfo] = {}

        # Medical histories: {history_id: MedicalHistoryInfo}
        self.medical_histories: Dict[str, MedicalHistoryInfo] = {}

        # Staff: {staff_id: StaffInfo}
        self.staff: Dict[str, StaffInfo] = {}

        # Roles: {role_name: RoleDefinitionInfo}
        self.roles: Dict[str, RoleDefinitionInfo] = {}

        # Constraints:
        # - Patients must have unique patient_id values
        # - Access to patient data is restricted and determined by staff role and defined permissions
        # - Only authorized staff may view or edit sensitive information (e.g., medical_history)
        # - Admissions are tied to valid patient IDs and must have logical admission/discharge dates
        # - Medical history is linked to patients and can only be modified by staff with appropriate permissions

    @staticmethod
    def _parse_supported_datetime(value: str):
        if not isinstance(value, str):
            raise ValueError("Invalid date value")
        text = value.strip()
        if not text:
            raise ValueError("Empty date value")
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%SZ"):
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("Unsupported date format") from exc

    def check_staff_access_rights(self, staff_id: str, data_field: str) -> dict:
        """
        Verify if a staff member has access to a specific patient data field,
        based on their role and the permissions defined for that role.

        Args:
            staff_id (str): ID of the staff member.
            data_field (str): Field of patient data being requested (e.g., 'medical_history').

        Returns:
            dict:
                - On success:
                    { "success": True, "access_granted": bool }
                - On failure:
                    { "success": False, "error": str }

        Constraints:
            - Staff must exist.
            - The staff's role must have a role definition entry.
            - Access is granted only if the data field is present in the permissions list for the role.
        """
        staff = self.staff.get(staff_id)
        if not staff:
            return { "success": False, "error": "Staff not found" }

        role_name = staff.get("role")
        role_def = self.roles.get(role_name)
        if not role_def:
            return { "success": False, "error": "Staff role definition not found" }

        permissions = role_def.get("permissions", [])
        access_granted = data_field in permissions

        return { "success": True, "access_granted": access_granted }

    def get_patient_by_id(self, patient_id: str) -> dict:
        """
        Retrieve all demographic and reference information for a given patient ID.

        Args:
            patient_id (str): The patient ID.

        Returns:
            dict: {
                "success": True,
                "data": PatientInfo  # demographics and reference info,
            }
            or
            {
                "success": False,
                "error": "Patient not found"
            }

        Constraints:
            - patient_id must exist in the system.
            - No permission check is enforced for demographic/reference info.
        """
        patient = self.patients.get(patient_id)
        if not patient:
            return { "success": False, "error": "Patient not found" }
        return { "success": True, "data": patient }

    def get_patient_hometown(self, patient_id: str, staff_id: str) -> dict:
        """
        Retrieve the hometown of a patient, verifying staff access rights.

        Args:
            patient_id (str): The unique identifier for the patient.
            staff_id (str): The unique identifier for the staff performing the query.

        Returns:
            dict: 
                If allowed:
                    {
                        "success": True,
                        "data": "<hometown>"
                    }
                If not allowed or input invalid:
                    {
                        "success": False,
                        "error": "<reason>"
                    }

        Constraints:
            - Patient must exist.
            - Staff must exist.
            - Staff's role (and the associated permissions) must grant view access to patient demographic information
              (permission 'view_patient_demographics' must be present for access).
        """

        # Check patient exists
        patient = self.patients.get(patient_id)
        if patient is None:
            return { "success": False, "error": "Patient not found" }

        # Check staff exists
        staff = self.staff.get(staff_id)
        if staff is None:
            return { "success": False, "error": "Staff not found" }

        # Check staff's role and permissions
        role_name = staff.get("role")
        if not role_name:
            return { "success": False, "error": "Staff role not defined" }

        role_info = self.roles.get(role_name)
        if not role_info or "permissions" not in role_info:
            return { "success": False, "error": "Staff role definition missing or incomplete" }

        permissions = role_info["permissions"]
        if "view_patient_demographics" not in permissions:
            return { "success": False, "error": "Permission denied" }

        # Passed all checks: return hometown
        return { "success": True, "data": patient["hometown"] }

    def list_all_patients(self) -> dict:
        """
        List all patient records stored in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[PatientInfo]   # List of all patients' info, possibly empty
            }

        Constraints:
            - No parameters required.
            - Returns all patient records present in the system.
        """
        return {"success": True, "data": list(self.patients.values())}

    def get_admission_by_id(self, admission_id: str) -> dict:
        """
        Retrieve details about a specific admission using admission_id.

        Args:
            admission_id (str): The unique identifier of the admission record.

        Returns:
            dict: {
                "success": True,
                "data": AdmissionInfo,  # Admission details if found
            }
            OR
            {
                "success": False,
                "error": str  # Error description if admission not found
            }

        Constraints:
            - The specified admission_id must exist in the admissions registry.
            - No access permissions check is performed for this simple query.
        """
        admission = self.admissions.get(admission_id)
        if not admission:
            return {"success": False, "error": "Admission not found"}
        return {"success": True, "data": admission}

    def list_patient_admissions(self, patient_id: str) -> dict:
        """
        Retrieve a list of all admissions for a given patient.

        Args:
            patient_id (str): The ID of the patient whose admissions are being retrieved.

        Returns:
            dict:
                If the patient exists:
                {
                    "success": True,
                    "data": List[AdmissionInfo]  # List of admissions (empty if none)
                }
                If patient does not exist:
                {
                    "success": False,
                    "error": "Patient not found"
                }

        Constraints:
            - patient_id must reference an existing patient in the system.
        """
        if patient_id not in self.patients:
            return {"success": False, "error": "Patient not found"}

        admissions_list = [
            admission for admission in self.admissions.values()
            if admission["patient_id"] == patient_id
        ]

        return {"success": True, "data": admissions_list}

    def get_current_admission_for_patient(self, patient_id: str) -> dict:
        """
        Retrieve the current (active) admission record for the specified patient.

        Args:
            patient_id (str): The unique identifier for the patient.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": AdmissionInfo  # Current admission record info
                    }
                - On failure:
                    {
                        "success": False,
                        "error": str  # Description of the error
                    }

        Constraints:
            - Patient must exist in the system.
            - Patient must have a non-empty current_admission_reference.
            - The referenced admission must exist in admissions.
        """
        patient = self.patients.get(patient_id)
        if not patient:
            return {"success": False, "error": "Patient not found."}

        adm_ref = patient.get("current_admission_reference")
        if not adm_ref:
            return {"success": False, "error": "No current admission for this patient."}

        admission = self.admissions.get(adm_ref)
        if not admission:
            return {"success": False, "error": "Current admission record not found."}

        return {"success": True, "data": admission}

    def get_medical_history_by_id(self, history_id: str, requesting_staff_id: str) -> dict:
        """
        Retrieve the complete medical history for a patient using `history_id`, enforcing access controls.

        Args:
            history_id (str): Identifier for the medical history entry.
            requesting_staff_id (str): The staff ID of the user requesting the information.

        Returns:
            dict: 
                { "success": True, "data": MedicalHistoryInfo }
                OR
                { "success": False, "error": str }
    
        Constraints:
            - Only staff with permission to view medical history may access this information.
        """
        # Check if history exists
        if history_id not in self.medical_histories:
            return { "success": False, "error": "Medical history record does not exist." }

        # Check if staff exists
        staff_info = self.staff.get(requesting_staff_id)
        if not staff_info:
            return { "success": False, "error": "Requesting staff member not found." }

        role_name = staff_info["role"]
        role_def = self.roles.get(role_name)
        if not role_def:
            return { "success": False, "error": "Role definition not found for staff." }

        # Enforce permission check (assume permission name is 'view_medical_history')
        if "view_medical_history" not in role_def.get("permissions", []):
            return { "success": False, "error": "Permission denied: insufficient privileges to view medical history." }

        history_info = self.medical_histories[history_id]
        return { "success": True, "data": history_info }

    def get_patient_medical_history(self, staff_id: str, patient_id: str) -> dict:
        """
        Fetch a patient's medical history (MedicalHistoryInfo) given a patient ID,
        after checking that the requesting staff member is authorized to view such records.

        Args:
            staff_id (str): The staff member's unique ID requesting the information.
            patient_id (str): The patient's unique ID whose medical history to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": MedicalHistoryInfo
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - staff_id must correspond to a valid staff member.
            - The staff's role must have the "view_medical_history" permission.
            - Patient and their medical history must exist.
        """
        # Validate staff_id
        staff = self.staff.get(staff_id)
        if not staff:
            return { "success": False, "error": "Invalid staff_id" }
        # Get staff role
        role_name = staff.get("role")
        role_def = self.roles.get(role_name)
        if not role_def:
            return { "success": False, "error": "Staff role definition not found" }
        # Check for required permission
        permissions = role_def.get("permissions", [])
        if "view_medical_history" not in permissions:
            return { "success": False, "error": "Insufficient permission to view medical history" }

        # Validate patient_id
        patient = self.patients.get(patient_id)
        if not patient:
            return { "success": False, "error": "Patient not found" }
        # Get the medical history reference
        history_id = patient.get("medical_history_reference")
        if not history_id:
            return { "success": False, "error": "No medical history reference for patient" }
        # Fetch the medical history
        medical_history = self.medical_histories.get(history_id)
        if not medical_history:
            return { "success": False, "error": "Medical history not found" }

        return { "success": True, "data": medical_history }

    def get_staff_by_id(self, staff_id: str) -> dict:
        """
        Fetch details of a staff member by their `staff_id`.

        Args:
            staff_id (str): Unique identifier for the staff member.

        Returns:
            dict: {
                "success": True,
                "data": StaffInfo
            }
            OR
            {
                "success": False,
                "error": "Staff member not found"
            }
        Constraints:
            - staff_id must exist in the system. If it does not, the operation fails.
        """
        staff_info = self.staff.get(staff_id)
        if staff_info is None:
            return {"success": False, "error": "Staff member not found"}
        return {"success": True, "data": staff_info}

    def list_all_staff(self) -> dict:
        """
        List all staff members present in the system.

        Args:
            None.

        Returns:
            dict:
                success (bool): Whether the operation succeeded.
                data (List[StaffInfo]): List of all staff member records; may be empty if no staff are registered.
        """
        staff_list = list(self.staff.values())
        return {
            "success": True,
            "data": staff_list
        }

    def get_role_definition(self, role_name: str) -> dict:
        """
        Retrieve the permissions and description of a role by its role_name.

        Args:
            role_name (str): The name of the role to query.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": {
                            "role_name": str,
                            "permissions": List[str],
                            "description": str
                        }
                    }
                On failure:
                    {
                        "success": False,
                        "error": str
                    }

        Constraints:
            - The role_name must correspond to an existing role in the system.
            - No permission checks are performed for this query operation.
        """
        if not role_name or role_name not in self.roles:
            return {"success": False, "error": "Role does not exist."}

        role_info = self.roles[role_name]
        return {
            "success": True,
            "data": {
                "role_name": role_info["role_name"],
                "permissions": role_info["permissions"],
                "description": role_info["description"]
            }
        }

    def add_new_patient(
        self,
        patient_id: str,
        name: str,
        birth_date: str,
        gender: str,
        hometown: str,
        address: str,
        contact_info: str,
        medical_history_reference: str,
        current_admission_reference: str
    ) -> dict:
        """
        Register a new patient with a unique patient_id and full demographic info.

        Args:
            patient_id (str): Unique patient identifier.
            name (str): Patient's name.
            birth_date (str): Patient's date of birth.
            gender (str): Patient's gender.
            hometown (str): Patient's hometown.
            address (str): Patient's address.
            contact_info (str): Patient's contact information.
            medical_history_reference (str): Reference ID for the medical history record.
            current_admission_reference (str): Reference ID for the current admission, or empty if none.

        Returns:
            dict: {
                "success": True,
                "message": "Patient <patient_id> added successfully"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - patient_id must be unique.
            - All fields are required.
        """
        if not patient_id:
            return {"success": False, "error": "patient_id is required"}
        if patient_id in self.patients:
            return {"success": False, "error": f"Patient ID '{patient_id}' already exists"}

        # Construct the patient record
        new_patient = {
            "patient_id": patient_id,
            "name": name,
            "birth_date": birth_date,
            "gender": gender,
            "hometown": hometown,
            "address": address,
            "contact_info": contact_info,
            "medical_history_reference": medical_history_reference,
            "current_admission_reference": current_admission_reference,
        }
        self.patients[patient_id] = new_patient
        return {"success": True, "message": f"Patient {patient_id} added successfully"}

    def update_patient_info(self, staff_id: str, patient_id: str, updates: dict) -> dict:
        """
        Edit demographic information for an existing patient, subject to access control.

        Args:
            staff_id (str): ID of the staff member attempting the update.
            patient_id (str): ID of the patient whose info is to be updated.
            updates (dict): Dictionary of allowed demographic fields to update, e.g.:
                {
                    "address": "New address",
                    "contact_info": "555-1234",
                    ...
                }

        Returns:
            dict:
                - On success: {"success": True, "message": "Patient information updated successfully."}
                - On failure: {"success": False, "error": "..."}
    
        Constraints:
            - Only authorized staff (roles with 'edit_patient_info' permission) may perform this update.
            - Cannot edit core id/reference fields (['patient_id', 'medical_history_reference', 'current_admission_reference']).
            - Patient and staff must exist.
        """
        # Validate staff
        staff = self.staff.get(staff_id)
        if not staff:
            return { "success": False, "error": "Unauthorized or staff not found." }
    
        # Lookup role and permissions
        role_def = self.roles.get(staff["role"])
        if not role_def or "edit_patient_info" not in role_def.get("permissions", []):
            return { "success": False, "error": "Unauthorized or staff not found." }
    
        # Validate patient
        patient = self.patients.get(patient_id)
        if not patient:
            return { "success": False, "error": "Patient not found." }
    
        # Fields that should NOT be changed here
        forbidden_fields = {"patient_id", "medical_history_reference", "current_admission_reference"}
        if any(field in forbidden_fields for field in updates):
            return { "success": False, "error": "Attempt to modify restricted field(s)." }
    
        # Only allow updates to fields that exist in PatientInfo and are not forbidden
        allowed_fields = set(patient.keys()) - forbidden_fields
        for key, value in updates.items():
            if key not in allowed_fields:
                return { "success": False, "error": f"Field '{key}' cannot be updated." }
            self.patients[patient_id][key] = value
    
        return { "success": True, "message": "Patient information updated successfully." }

    def add_admission_record(
        self,
        admission_id: str,
        patient_id: str,
        admission_date: str,
        discharge_date: str,
        room_number: str,
        attending_physician_id: str,
        status: str,
    ) -> dict:
        """
        Adds a new admission record for a patient.

        Args:
            admission_id (str): Unique identifier for the admission.
            patient_id (str): ID of the patient (must exist).
            admission_date (str): Date of admission (ISO format).
            discharge_date (str): Date of discharge (ISO format, can be empty or None if not discharged yet).
            room_number (str): Room assigned.
            attending_physician_id (str): Staff ID of attending physician.
            status (str): Admission status.

        Returns:
            dict: 
              - On success: {"success": True, "message": "Admission record for patient ... added successfully."}
              - On failure: {"success": False, "error": "..."}
    
        Constraints:
            - Patient ID must exist.
            - Admission ID must be unique.
            - Admission date must be provided.
            - Discharge date (if provided) cannot be before admission date.
        """
        if not all([admission_id, patient_id, admission_date, room_number, attending_physician_id, status]):
            return {"success": False, "error": "All fields except discharge_date must be provided and non-empty."}

        if admission_id in self.admissions:
            return {"success": False, "error": "Admission ID already exists in the system."}

        if patient_id not in self.patients:
            return {"success": False, "error": "Patient ID does not exist."}

        # (Optional) Validate attending physician exists
        if attending_physician_id not in self.staff:
            return {"success": False, "error": "Attending physician ID does not exist."}

        # Validate dates: assume ISO (YYYY-MM-DD) format
        try:
            ad_date = datetime.strptime(admission_date, "%Y-%m-%d")
            if discharge_date and discharge_date.strip():
                dis_date = datetime.strptime(discharge_date, "%Y-%m-%d")
                if dis_date < ad_date:
                    return {"success": False, "error": "Discharge date cannot be before admission date."}
            else:
                discharge_date = "" # Normalize empty/null value
        except Exception:
            return {"success": False, "error": "Invalid date format. Must be YYYY-MM-DD."}

        # Build and insert new admission record
        admission: AdmissionInfo = {
            "admission_id": admission_id,
            "patient_id": patient_id,
            "admission_date": admission_date,
            "discharge_date": discharge_date,
            "room_number": room_number,
            "attending_physician_id": attending_physician_id,
            "status": status
        }
        self.admissions[admission_id] = admission

        # Optionally, update patient's current_admission_reference
        self.patients[patient_id]["current_admission_reference"] = admission_id

        return {
            "success": True,
            "message": f"Admission record for patient {patient_id} added successfully."
        }

    def update_admission_record(
        self,
        staff_id: str,
        admission_id: str,
        updates: dict
    ) -> dict:
        """
        Modify details of an admission (e.g., discharge patient, change physician), enforcing logical time constraints.

        Args:
            staff_id (str): Staff member requesting the update (permission is checked).
            admission_id (str): The admission record to be updated.
            updates (dict): Dictionary of fields to update. Allowed fields include:
                - admission_date, discharge_date, room_number, attending_physician_id, status

        Returns:
            dict:
                If success: { "success": True, "message": "Admission record updated successfully" }
                If failure: { "success": False, "error": <reason> }

        Constraints:
            - Only staff with 'edit_admission' permission (via their role) may update admissions.
            - Logical time: discharge_date must not be before admission_date.
            - Only provided fields are updated.
            - Admission_id must exist.
            - Staff_id must exist.
        """
        # Check staff existence
        staff = self.staff.get(staff_id)
        if not staff:
            return {"success": False, "error": "Staff member not found"}

        # Look up staff role and permissions
        role_name = staff.get("role")
        role_def = self.roles.get(role_name)
        if not role_def or "edit_admission" not in role_def.get("permissions", []):
            return {"success": False, "error": "Permission denied"}

        # Check admission existence
        admission = self.admissions.get(admission_id)
        if not admission:
            return {"success": False, "error": "Admission record not found"}

        # Prepare updated values
        new_admission = admission.copy()
        allowed_fields = {
            "admission_date", "discharge_date", "room_number",
            "attending_physician_id", "status"
        }
        for k, v in updates.items():
            if k in allowed_fields:
                new_admission[k] = v

        # Logical date constraint
        adm_date = new_admission.get("admission_date")
        dis_date = new_admission.get("discharge_date")
        if adm_date and dis_date:
            try:
                adm_dt = self._parse_supported_datetime(adm_date)
                dis_dt = self._parse_supported_datetime(dis_date)
                if dis_dt < adm_dt:
                    return {
                        "success": False,
                        "error": "Discharge date cannot be before admission date"
                    }
            except Exception:
                return {
                    "success": False,
                    "error": "Invalid date format; expected YYYY-MM-DD"
                }

        # Apply update
        self.admissions[admission_id] = new_admission
        return {"success": True, "message": "Admission record updated successfully"}

    def add_medical_history_entry(
        self, 
        staff_id: str,
        patient_id: str,
        diagnoses: List[str],
        allergies: List[str],
        medications: List[str],
        procedures: List[str],
        notes: str
    ) -> dict:
        """
        Insert a new medical history entry for an existing patient. Permission-required.
    
        Args:
            staff_id (str): The staff member attempting to add the entry.
            patient_id (str): The patient to which the medical history belongs.
            diagnoses (List[str])
            allergies (List[str])
            medications (List[str])
            procedures (List[str])
            notes (str)
        
        Returns:
            dict:
                - success: True/False
                - message: Description if successful
                - history_id: str (if successful)
                - error: Description if failed
            
        Constraints:
            - Only staff with appropriate permission ("add_medical_history") may perform this operation.
            - The patient must exist.
            - Medical history entry will be linked to the provided patient_id and assigned a unique history_id.
        """
        # 1. Validate staff_id and permissions
        staff_info = self.staff.get(staff_id)
        if not staff_info:
            return { "success": False, "error": "Staff ID not found" }
    
        staff_role = staff_info.get("role")
        if staff_role not in self.roles:
            return { "success": False, "error": "Staff role definition missing" }
    
        role_def = self.roles[staff_role]
        permissions = role_def.get("permissions", [])
        if "add_medical_history" not in permissions:
            return { "success": False, "error": "Permission denied: cannot add medical history entry" }
    
        # 2. Validate patient exists
        if patient_id not in self.patients:
            return { "success": False, "error": "Patient not found" }
    
        # 3. Generate unique history_id
        history_id = str(uuid.uuid4())
        while history_id in self.medical_histories:
            history_id = str(uuid.uuid4())
    
        # 4. Create MedicalHistory entry
        new_entry: MedicalHistoryInfo = {
            "history_id": history_id,
            "patient_id": patient_id,
            "diagnoses": diagnoses,
            "allergies": allergies,
            "medications": medications,
            "procedures": procedures,
            "notes": notes
        }
        self.medical_histories[history_id] = new_entry

        # 5. Optionally, update patient's medical_history_reference if appropriate.
        # If system design assumes only reference to most recent or latest:
        self.patients[patient_id]["medical_history_reference"] = history_id

        return {
            "success": True,
            "message": "Medical history entry added",
            "history_id": history_id
        }

    def update_medical_history_entry(
        self,
        staff_id: str,
        history_id: str,
        diagnoses: list = None,
        allergies: list = None,
        medications: list = None,
        procedures: list = None,
        notes: str = None
    ) -> dict:
        """
        Edit diagnoses, allergies, medications, procedures, or notes for a medical history,
        checking that the staff member has appropriate permissions.

        Args:
            staff_id (str): ID of the staff performing the operation.
            history_id (str): ID of the medical history entry to update.
            diagnoses (list, optional): New diagnoses list.
            allergies (list, optional): New allergies list.
            medications (list, optional): New medications list.
            procedures (list, optional): New procedures list.
            notes (str, optional): New notes string.

        Returns:
            dict: {
                "success": True,
                "message": "Medical history updated successfully"
            }
            or
            {
                "success": False,
                "error": "Reason for failure"
            }

        Constraints:
            - Staff must exist and have a role with "edit_medical_history" permission.
            - Medical history entry must exist.
            - At least one updatable field must be provided.
        """
        # 1. Verify staff exists
        if staff_id not in self.staff:
            return {"success": False, "error": "Staff member not found"}

        staff_info = self.staff[staff_id]
        staff_role = staff_info['role']

        # 2. Verify role and permissions
        if staff_role not in self.roles:
            return {"success": False, "error": "Staff role definition not found"}

        role_info = self.roles[staff_role]
        permissions = role_info.get("permissions", [])

        if "edit_medical_history" not in permissions:
            return {"success": False, "error": "Permission denied: cannot edit medical history"}

        # 3. Verify medical_history exists
        if history_id not in self.medical_histories:
            return {"success": False, "error": "Medical history entry not found"}

        history_entry = self.medical_histories[history_id]

        # 4. Check for at least one updatable field
        update_fields = ["diagnoses", "allergies", "medications", "procedures", "notes"]
        provided = any([
            diagnoses is not None,
            allergies is not None,
            medications is not None,
            procedures is not None,
            notes is not None,
        ])
        if not provided:
            return {"success": False, "error": "No fields provided for update"}

        # 5. Perform updates (None means skip)
        if diagnoses is not None:
            history_entry['diagnoses'] = diagnoses
        if allergies is not None:
            history_entry['allergies'] = allergies
        if medications is not None:
            history_entry['medications'] = medications
        if procedures is not None:
            history_entry['procedures'] = procedures
        if notes is not None:
            history_entry['notes'] = notes

        # 6. Save back (not strictly needed since dict is mutable, but explicit)
        self.medical_histories[history_id] = history_entry

        return {"success": True, "message": "Medical history updated successfully"}

    def add_staff_member(self, staff_id: str, name: str, role: str, department: str, access_level: str) -> dict:
        """
        Register a new staff member, assigning staff_id, name, role, department, and access level.

        Args:
            staff_id (str): Unique identifier for the staff member.
            name (str): Staff member's name.
            role (str): Role to assign; must exist in the roles table.
            department (str): Department to assign.
            access_level (str): Staff member's access level.

        Returns:
            dict: {
                "success": True,
                "message": "Staff member <staff_id> added successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - staff_id must be unique.
            - role must exist in roles.
            - All required fields must be non-empty.
        """
        # Check for missing or empty required fields
        if not all([staff_id, name, role, department, access_level]):
            return {"success": False, "error": "All staff member fields are required and must not be empty."}
    
        # Check staff_id uniqueness
        if staff_id in self.staff:
            return {"success": False, "error": f"Staff ID '{staff_id}' already exists."}
    
        # Check that role exists
        if role not in self.roles:
            return {"success": False, "error": f"Role '{role}' does not exist."}

        new_staff: StaffInfo = {
            "staff_id": staff_id,
            "name": name,
            "role": role,
            "department": department,
            "access_level": access_level
        }
        self.staff[staff_id] = new_staff

        return {"success": True, "message": f"Staff member '{staff_id}' added successfully."}

    def update_staff_info(
        self,
        staff_id: str,
        name: str = None,
        role: str = None,
        department: str = None,
        access_level: str = None
    ) -> dict:
        """
        Change staff details (role, department, name, access_level) for a given staff member.

        Args:
            staff_id (str): The ID of the staff member to update.
            name (str, optional): New name for the staff member.
            role (str, optional): New role for the staff member (must exist).
            department (str, optional): New department for the staff member.
            access_level (str, optional): New access level for the staff member.

        Returns:
            dict:
                - On success: { "success": True, "message": "Staff information updated for <staff_id>" }
                - On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - staff_id must exist.
            - If updating role, the new role must exist in self.roles.
            - No update fields provided is considered an error.
        """
        if staff_id not in self.staff:
            return { "success": False, "error": "Staff member does not exist" }

        # Check if any updates are provided
        if all(arg is None for arg in [name, role, department, access_level]):
            return { "success": False, "error": "No update fields provided" }

        staff_info = self.staff[staff_id]

        # Integrity check: if changing role, it must exist
        if role is not None:
            if role not in self.roles:
                return { "success": False, "error": "The specified role does not exist" }
            staff_info["role"] = role

        # Update fields as provided
        if name is not None:
            if not isinstance(name, str) or not name.strip():
                return { "success": False, "error": "Name must be a non-empty string" }
            staff_info["name"] = name.strip()

        if department is not None:
            if not isinstance(department, str) or not department.strip():
                return { "success": False, "error": "Department must be a non-empty string" }
            staff_info["department"] = department.strip()

        if access_level is not None:
            if not isinstance(access_level, str) or not access_level.strip():
                return { "success": False, "error": "Access level must be a non-empty string" }
            staff_info["access_level"] = access_level.strip()

        self.staff[staff_id] = staff_info  # Redundant, but ensures dict consistency

        return { "success": True, "message": f"Staff information updated for {staff_id}" }

    def add_role_definition(self, role_name: str, permissions: list, description: str) -> dict:
        """
        Create and register a new staff role with defined permissions in the system.

        Args:
            role_name (str): Unique name of the role to add.
            permissions (list of str): Permissions to assign to this role.
            description (str): Description of the new role.

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "message": "Role '<role_name>' created successfully"
                }
                On failure: {
                    "success": False,
                    "error": <reason>
                }

        Constraints:
            - Role names must be unique (not already present in self.roles).
            - Permissions should be a list of strings (should not be empty).
        """
        if not isinstance(role_name, str) or not role_name.strip():
            return {"success": False, "error": "Role name must be a non-empty string"}
        if role_name in self.roles:
            return {"success": False, "error": "Role name already exists"}
        if not isinstance(permissions, list) or not all(isinstance(p, str) for p in permissions):
            return {"success": False, "error": "Permissions must be a list of strings"}
        if not permissions:
            return {"success": False, "error": "Permissions list cannot be empty"}
        if not isinstance(description, str) or not description.strip():
            return {"success": False, "error": "Description must be a non-empty string"}

        self.roles[role_name] = {
            "role_name": role_name,
            "permissions": permissions,
            "description": description
        }
        return {"success": True, "message": f"Role '{role_name}' created successfully"}

    def update_role_permissions(self, role_name: str, new_permissions: list) -> dict:
        """
        Alter the permissions associated with a given role.

        Args:
            role_name (str): The name of the role whose permissions are to be updated.
            new_permissions (list of str): The new permissions list to set for this role.

        Returns:
            dict: {
                "success": True,
                "message": str  # describes the successful update
            }
            or
            {
                "success": False,
                "error": str  # describes the reason for failure
            }

        Constraints:
            - The specified role must exist.
            - new_permissions must be a list of strings.
        """

        # Check that role exists
        if role_name not in self.roles:
            return { "success": False, "error": "Role not found." }

        # Validate permissions format - must be a list of strings
        if not isinstance(new_permissions, list) or not all(isinstance(p, str) for p in new_permissions):
            return { "success": False, "error": "Invalid permissions format." }

        # Update the permissions
        self.roles[role_name]["permissions"] = new_permissions

        return {
            "success": True,
            "message": f"Permissions for role '{role_name}' updated."
        }

    def delete_patient_record(self, patient_id: str, staff_id: str) -> dict:
        """
        Remove a patient record and all associated admissions and medical history from the system.
        Only staff with 'delete_patient' permission may perform this operation.

        Args:
            patient_id (str): The ID of the patient to delete.
            staff_id (str): The ID of the staff performing the operation.

        Returns:
            dict: {
                "success": True,
                "message": str,
            }
            or
            {
                "success": False,
                "error": str,
            }

        Constraints:
            - Patient must exist.
            - Staff must exist and have permission to delete patient records.
            - All admissions and medical histories linked to the patient are also deleted.
        """
        # Check staff exists
        staff = self.staff.get(staff_id)
        if not staff:
            return {"success": False, "error": "Staff member not found"}

        staff_role = staff.get("role")
        role_def = self.roles.get(staff_role)
        if not role_def:
            return {"success": False, "error": "Staff role definition not found"}

        permissions = role_def.get("permissions", [])
        if "delete_patient" not in permissions:
            return {"success": False, "error": "Permission denied: staff lacks delete_patient right"}

        # Check patient exists
        if patient_id not in self.patients:
            return {"success": False, "error": "Patient not found"}

        # Delete patient record
        del self.patients[patient_id]

        # Delete related admissions
        admissions_to_delete = [aid for aid, adm in self.admissions.items() if adm["patient_id"] == patient_id]
        for aid in admissions_to_delete:
            del self.admissions[aid]

        # Delete related medical histories
        histories_to_delete = [hid for hid, mh in self.medical_histories.items() if mh["patient_id"] == patient_id]
        for hid in histories_to_delete:
            del self.medical_histories[hid]

        return {
            "success": True,
            "message": "Patient and related records deleted"
        }


class HospitalPatientInfoManagementSystem(BaseEnv):
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

    def check_staff_access_rights(self, **kwargs):
        return self._call_inner_tool('check_staff_access_rights', kwargs)

    def get_patient_by_id(self, **kwargs):
        return self._call_inner_tool('get_patient_by_id', kwargs)

    def get_patient_hometown(self, **kwargs):
        return self._call_inner_tool('get_patient_hometown', kwargs)

    def list_all_patients(self, **kwargs):
        return self._call_inner_tool('list_all_patients', kwargs)

    def get_admission_by_id(self, **kwargs):
        return self._call_inner_tool('get_admission_by_id', kwargs)

    def list_patient_admissions(self, **kwargs):
        return self._call_inner_tool('list_patient_admissions', kwargs)

    def get_current_admission_for_patient(self, **kwargs):
        return self._call_inner_tool('get_current_admission_for_patient', kwargs)

    def get_medical_history_by_id(self, **kwargs):
        return self._call_inner_tool('get_medical_history_by_id', kwargs)

    def get_patient_medical_history(self, **kwargs):
        return self._call_inner_tool('get_patient_medical_history', kwargs)

    def get_staff_by_id(self, **kwargs):
        return self._call_inner_tool('get_staff_by_id', kwargs)

    def list_all_staff(self, **kwargs):
        return self._call_inner_tool('list_all_staff', kwargs)

    def get_role_definition(self, **kwargs):
        return self._call_inner_tool('get_role_definition', kwargs)

    def add_new_patient(self, **kwargs):
        return self._call_inner_tool('add_new_patient', kwargs)

    def update_patient_info(self, **kwargs):
        return self._call_inner_tool('update_patient_info', kwargs)

    def add_admission_record(self, **kwargs):
        return self._call_inner_tool('add_admission_record', kwargs)

    def update_admission_record(self, **kwargs):
        return self._call_inner_tool('update_admission_record', kwargs)

    def add_medical_history_entry(self, **kwargs):
        return self._call_inner_tool('add_medical_history_entry', kwargs)

    def update_medical_history_entry(self, **kwargs):
        return self._call_inner_tool('update_medical_history_entry', kwargs)

    def add_staff_member(self, **kwargs):
        return self._call_inner_tool('add_staff_member', kwargs)

    def update_staff_info(self, **kwargs):
        return self._call_inner_tool('update_staff_info', kwargs)

    def add_role_definition(self, **kwargs):
        return self._call_inner_tool('add_role_definition', kwargs)

    def update_role_permissions(self, **kwargs):
        return self._call_inner_tool('update_role_permissions', kwargs)

    def delete_patient_record(self, **kwargs):
        return self._call_inner_tool('delete_patient_record', kwargs)
