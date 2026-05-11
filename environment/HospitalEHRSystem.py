# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
from datetime import datetime



class PatientInfo(TypedDict):
    patient_id: str
    name: str
    date_of_birth: str
    demographics: str
    contact_information: str

class PatientStatusEntryInfo(TypedDict):
    status_id: str
    patient_id: str
    timestamp: str
    status_description: str
    updated_by: str  # user_id of the AuthorizedUser

class ClinicalEncounterInfo(TypedDict):
    encounter_id: str
    patient_id: str
    encounter_type: str
    date: str
    attending_provider: str

class AuthorizedUserInfo(TypedDict):
    user_id: str
    name: str
    role: str
    access_level: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment state for the Hospital EHR system.
        """

        # Patients: {patient_id: PatientInfo}
        self.patients: Dict[str, PatientInfo] = {}

        # Patient Status History: {status_id: PatientStatusEntryInfo}
        # (can also be grouped per patient in future)
        self.patient_status_entries: Dict[str, PatientStatusEntryInfo] = {}

        # Clinical Encounters: {encounter_id: ClinicalEncounterInfo}
        self.clinical_encounters: Dict[str, ClinicalEncounterInfo] = {}

        # Authorized Users: {user_id: AuthorizedUserInfo}
        self.authorized_users: Dict[str, AuthorizedUserInfo] = {}

        # --- Constraints (to be enforced in methods) ---
        # - Each PatientStatusEntry must be linked to a valid patient_id.
        # - Timestamps of status updates must be in chronological order when rendered in the patient's record.
        # - Only users with appropriate access_level can create PatientStatusEntry records.
        # - All updates must be auditable (including updated_by information).
        # - Patient identifiers (patient_id) must be unique within the system.

    def get_patient_by_id(self, patient_id: str) -> dict:
        """
        Retrieve all demographic and contact info for a specific patient by patient_id.

        Args:
            patient_id (str): The unique identifier of the patient.

        Returns:
            dict: 
                If found:
                    {
                        "success": True,
                        "data": PatientInfo
                    }
                If not found:
                    {
                        "success": False,
                        "error": "Patient not found"
                    }

        Constraints:
            - patient_id must refer to a PatientInfo in the system.
        """
        patient = self.patients.get(patient_id)
        if patient is None:
            return {"success": False, "error": "Patient not found"}
        return {"success": True, "data": patient}

    def list_all_patients(self) -> dict:
        """
        Retrieve the list of all patients currently in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[PatientInfo]  # List of all patient information records (may be empty if no patients).
            }
        """
        data = list(self.patients.values())
        return { "success": True, "data": data }

    def get_patient_status_history(self, patient_id: str) -> dict:
        """
        Retrieve all PatientStatusEntry records for the specified patient, sorted by timestamp (chronological order).

        Args:
            patient_id (str): Unique identifier of the patient.

        Returns:
            dict: {
                "success": True,
                "data": List[PatientStatusEntryInfo]  # list is ordered by timestamp ascending, may be empty
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., patient does not exist
            }

        Constraints:
            - patient_id must exist in self.patients.
            - Only PatientStatusEntry records linked to this patient_id are returned, sorted by timestamp.
        """
        if patient_id not in self.patients:
            return { "success": False, "error": "Patient does not exist" }

        # Gather all status entries for the patient
        status_entries = [
            entry for entry in self.patient_status_entries.values()
            if entry["patient_id"] == patient_id and not entry.get("deleted", False)
        ]

        # Sort by timestamp (assuming ISO 8601 or sortable string format)
        status_entries.sort(key=lambda entry: entry["timestamp"])

        return { "success": True, "data": status_entries }

    def get_latest_patient_status(self, patient_id: str) -> dict:
        """
        Retrieve the most recent PatientStatusEntry for a patient by patient_id.

        Args:
            patient_id (str): Unique identifier for the patient.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": PatientStatusEntryInfo  # Most recent status entry
                    }
                On error:
                    {
                        "success": False,
                        "error": "Patient not found" | "No status entries for this patient"
                    }

        Constraints:
            - patient_id must exist in the patients dictionary.
            - Returns the status entry with the latest timestamp.
        """
        if patient_id not in self.patients:
            return { "success": False, "error": "Patient not found" }
    
        status_entries = [
            entry for entry in self.patient_status_entries.values()
            if entry["patient_id"] == patient_id and not entry.get("deleted", False)
        ]
        if not status_entries:
            return { "success": False, "error": "No status entries for this patient" }

        # Find latest by timestamp (assume lexicographical order is sufficient or timestamps are comparable)
        latest_entry = max(status_entries, key=lambda e: e["timestamp"])
        return { "success": True, "data": latest_entry }

    def get_clinical_encounters_by_patient(self, patient_id: str) -> dict:
        """
        Retrieve all ClinicalEncounter records for the specified patient.

        Args:
            patient_id (str): The ID of the patient whose clinical encounters are to be retrieved.

        Returns:
            dict: {
                "success": True,
                "data": List[ClinicalEncounterInfo]  # May be empty if no encounters for patient
            }
            or
            {
                "success": False,
                "error": str  # If the patient does not exist
            }

        Constraints:
            - The patient_id must exist in the system.
            - No permission check (query only).
        """
        if patient_id not in self.patients:
            return {"success": False, "error": "Patient does not exist"}

        matches = [
            encounter for encounter in self.clinical_encounters.values()
            if encounter["patient_id"] == patient_id
        ]
        return {"success": True, "data": matches}

    def get_status_entry_by_id(self, status_id: str) -> dict:
        """
        Retrieve a specific PatientStatusEntry by its status_id.

        Args:
            status_id (str): The unique identifier of the patient status entry.

        Returns:
            dict: {
                "success": True,
                "data": PatientStatusEntryInfo
            }
            OR
            {
                "success": False,
                "error": str  # Reason why retrieval failed
            }

        Constraints:
            - status_id must exist in the system.
        """
        entry = self.patient_status_entries.get(status_id)
        if not entry:
            return { "success": False, "error": "Status entry not found" }
        return { "success": True, "data": entry }

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve full info (name, role, access_level, user_id) for a specified AuthorizedUser by user_id.

        Args:
            user_id (str): The unique identifier for the authorized user.

        Returns:
            dict: {
                "success": True,
                "data": AuthorizedUserInfo
            }
            or
            {
                "success": False,
                "error": str   # If the user was not found
            }

        Constraints:
            - The user_id must exist in self.authorized_users.
        """
        user_info = self.authorized_users.get(user_id)
        if not user_info:
            return { "success": False, "error": "User not found" }

        return { "success": True, "data": user_info }

    def list_authorized_users(self) -> dict:
        """
        Retrieve the list of all authorized users in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[AuthorizedUserInfo],  # List of all authorized users (possibly empty)
            }
        """
        users = list(self.authorized_users.values())
        return {"success": True, "data": users}

    def check_user_access_level(self, user_id: str) -> dict:
        """
        Retrieve the access_level for a given user by user_id.
    
        Args:
            user_id (str): The unique identifier for the authorized user.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": {
                            "user_id": str,
                            "access_level": str
                        }
                    }
                - On failure:
                    {
                        "success": False,
                        "error": str
                    }
        Constraints:
            - user_id must exist in the authorized_users record.
        """
        user = self.authorized_users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }
        if "access_level" not in user:
            return { "success": False, "error": "Access level attribute missing for user" }
        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "access_level": user["access_level"]
            }
        }

    def is_patient_id_unique(self, patient_id: str) -> dict:
        """
        Determine if a proposed patient_id is unique (not present in the system).

        Args:
            patient_id (str): The patient ID to be checked.

        Returns:
            dict: {
                "success": True,
                "is_unique": bool,  # True if patient_id not used, False otherwise
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - patient_id must not be in use within self.patients.
            - If patient_id is empty, treat as not unique (return is_unique=False).
        """
        if not isinstance(patient_id, str) or not patient_id.strip():
            return { "success": True, "is_unique": False }

        is_unique = patient_id not in self.patients
        return { "success": True, "is_unique": is_unique }

    def add_patient_status_entry(
        self,
        status_id: str,
        patient_id: str,
        timestamp: str,
        status_description: str,
        updated_by: str,
    ) -> dict:
        """
        Create a new PatientStatusEntry for a patient, enforcing all constraints.
    
        Args:
            status_id (str): Unique identifier for the new status entry.
            patient_id (str): Patient ID this status entry belongs to.
            timestamp (str): The time the status update is made (ISO 8601 or compatible).
            status_description (str): Human-readable description of the status update.
            updated_by (str): user_id of the AuthorizedUser performing the update.
    
        Returns:
            dict: 
              On success: {
                "success": True, 
                "message": "PatientStatusEntry created for patient <patient_id>"
              }
              On error: {
                "success": False,
                "error": "<reason>"
              }
    
        Constraints:
            - patient_id must exist.
            - status_id must be unique.
            - updated_by is a valid authorized user with sufficient access level to create status.
            - Status-entry creation accepts access levels: "admin", "doctor", "clinical_editor", "nurse", "write", and temporary emergency "elevated".
            - All updates are auditable (include updated_by).
        """

        # 1. status_id must be unique
        if status_id in self.patient_status_entries:
            return {"success": False, "error": "status_id must be unique"}

        # 2. patient_id must exist
        if patient_id not in self.patients:
            return {"success": False, "error": "patient_id does not exist"}

        # 3. updated_by must be a valid authorized user
        user_info = self.authorized_users.get(updated_by)
        if not user_info:
            return {"success": False, "error": "updated_by (user_id) does not exist"}

        # 4. updated_by must have sufficient access level
        permitted_levels = {"write", "admin", "doctor", "nurse", "clinical_editor", "elevated"}
        if str(user_info.get("access_level", "")).lower() not in permitted_levels:
            return {"success": False, "error": "User does not have permission to add status entry"}

        # 5. (Optional: Chronological order warning, not required, do not enforce)
        # Fetch existing entries for the patient
        patient_entries = [
            entry for entry in self.patient_status_entries.values()
            if entry["patient_id"] == patient_id
        ]
        # If checking order, parse strings to comparable format (e.g., ISO8601)
        # NOT enforced in this implementation per prompt, but could check if desired

        # 6. Create and store the PatientStatusEntry
        entry = {
            "status_id": status_id,
            "patient_id": patient_id,
            "timestamp": timestamp,
            "status_description": status_description,
            "updated_by": updated_by,
        }
        self.patient_status_entries[status_id] = entry

        return {
            "success": True,
            "message": f"PatientStatusEntry created for patient {patient_id}"
        }

    def update_patient_status_entry(
        self,
        status_id: str,
        updated_fields: dict,
        updater_user_id: str
    ) -> dict:
        """
        Edit/correct an existing PatientStatusEntry if allowed and auditable.

        Args:
            status_id (str): Identifier of the status entry to update.
            updated_fields (dict): Dictionary of fields to update (eg: status_description, timestamp).
            updater_user_id (str): The user_id of the AuthorizedUser performing the update.

        Returns:
            dict: {
                "success": True,
                "message": "Patient status entry updated successfully"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Only users with appropriate access_level ("admin", "clinical_editor", "doctor", or "elevated") can edit entries.
            - status_id must exist.
            - patient_id, status_id should not be updatable.
            - Timestamps must not break chronological order for this patient's status history.
            - All updates must record who made the update ("updated_by").
        """
        # Check status entry exists
        status_entry = self.patient_status_entries.get(status_id)
        if not status_entry:
            return { "success": False, "error": "Status entry not found." }

        # Check updater is a valid authorized user
        user = self.authorized_users.get(updater_user_id)
        if not user:
            return { "success": False, "error": "Updater user not found." }

        # Check access_level -- must be an admin or a clinical/doctor-level editor.
        allowed_roles = {"admin", "clinical_editor", "doctor", "elevated"}
        user_access_level = str(user.get("access_level", "")).lower()
        if user_access_level not in allowed_roles:
            return { "success": False, "error": "User does not have permission to edit status entries." }

        # Deny attempt to edit immutable fields except allow admins to reattach a misfiled entry to the correct patient.
        immutable_fields = {"status_id"}
        if any(field in updated_fields for field in immutable_fields):
            return { "success": False, "error": "Cannot modify status_id in a status entry." }
        if "patient_id" in updated_fields:
            if user_access_level != "admin":
                return { "success": False, "error": "Cannot modify patient_id in a status entry unless user is admin." }
            if updated_fields["patient_id"] not in self.patients:
                return { "success": False, "error": "Updated patient_id does not exist." }

        # Prepare for possible timestamp validation
        patient_id = updated_fields.get("patient_id", status_entry['patient_id'])
        # Gather all of this patient's status entries
        entries = [
            e for e in self.patient_status_entries.values()
            if e["patient_id"] == patient_id and e["status_id"] != status_id and not e.get("deleted", False)
        ]
        # Sort by timestamp for this patient (ISO format, sort as string OK)
        entries_sorted = sorted(entries, key=lambda e: e["timestamp"])

        # Timestamp validation (if updated)
        if "timestamp" in updated_fields or "patient_id" in updated_fields:
            new_timestamp = updated_fields.get("timestamp", status_entry["timestamp"])
            prev_ts = None
            next_ts = None
            for entry in entries_sorted:
                if entry["timestamp"] <= new_timestamp:
                    prev_ts = entry["timestamp"]
                elif entry["timestamp"] > new_timestamp:
                    next_ts = entry["timestamp"]
                    break
            if prev_ts and new_timestamp < prev_ts:
                return {"success": False, "error": "Timestamp cannot be earlier than previous patient status entry."}
            if next_ts and new_timestamp > next_ts:
                return {"success": False, "error": "Timestamp cannot be later than next patient status entry."}

        # Only allow certain fields to be changed
        allowed_update_fields = {"status_description", "timestamp", "patient_id"}
        for field in updated_fields:
            if field not in allowed_update_fields:
                return { "success": False, "error": f"Cannot update field: {field}." }

        # Perform the update
        for field, value in updated_fields.items():
            status_entry[field] = value

        # Always update the updated_by field for audit
        status_entry['updated_by'] = updater_user_id

        # Write it back (not strictly necessary as dict is mutable, but explicitness is good)
        self.patient_status_entries[status_id] = status_entry

        return { "success": True, "message": "Patient status entry updated successfully" }

    def delete_patient_status_entry(self, status_id: str, requesting_user_id: str) -> dict:
        """
        Remove (soft-delete) a PatientStatusEntry, marking it as deleted for auditable correction,
        only if executed by an admin-level user.

        Args:
            status_id (str): The unique ID of the PatientStatusEntry to delete.
            requesting_user_id (str): The ID of the user requesting deletion (for authorization and auditing).

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Patient status entry <status_id> deleted (remains auditable)."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "reason for failure"
                    }

        Constraints:
            - Only users with 'admin' access_level may delete PatientStatusEntry records.
            - Deletion must be auditable; entry should not be hard-removed.
            - status_id must exist in the system.
            - requesting_user_id must reference a valid AuthorizedUser.
        """
        # Check existence of status entry
        entry = self.patient_status_entries.get(status_id)
        if not entry:
            return { "success": False, "error": "PatientStatusEntry does not exist" }

        # Check existence of requesting user
        user = self.authorized_users.get(requesting_user_id)
        if not user:
            return { "success": False, "error": "Requesting user does not exist" }

        # Check access level
        if user.get("access_level", "").lower() != "admin":
            return { "success": False, "error": "Permission denied: admin access required" }

        # Soft-delete: mark as deleted and record who did it and when.
        # If not already, add to each PatientStatusEntryInfo a 'deleted' flag.
        # (If the dict does not have a 'deleted' key yet, add it.)
        self.patient_status_entries[status_id]["deleted"] = True
        self.patient_status_entries[status_id]["deleted_by"] = requesting_user_id

        self.patient_status_entries[status_id]["deleted_at"] = datetime.now().isoformat()

        return {
            "success": True,
            "message": f"Patient status entry {status_id} deleted (remains auditable)."
        }

    def create_patient(
        self,
        patient_id: str,
        name: str,
        date_of_birth: str,
        demographics: str,
        contact_information: str
    ) -> dict:
        """
        Add a new patient record to the system, ensuring patient_id is unique.

        Args:
            patient_id (str): Unique identifier for the patient.
            name (str): Patient's full name.
            date_of_birth (str): Patient's date of birth.
            demographics (str): Demographic information.
            contact_information (str): Contact details.

        Returns:
            dict: {
                "success": True,
                "message": "Patient record created"
            }
            or
            {
                "success": False,
                "error": "Patient ID already exists"
            }
    
        Constraints:
            - patient_id must be unique in the system.
        """
        if patient_id in self.patients:
            return {"success": False, "error": "Patient ID already exists"}

        patient_info = {
            "patient_id": patient_id,
            "name": name,
            "date_of_birth": date_of_birth,
            "demographics": demographics,
            "contact_information": contact_information
        }

        self.patients[patient_id] = patient_info
        return {"success": True, "message": "Patient record created"}

    def edit_patient_info(
        self, 
        patient_id: str, 
        updated_fields: dict, 
        updated_by: str
    ) -> dict:
        """
        Update demographic or contact information for an existing patient.

        Args:
            patient_id (str): The unique ID of the patient whose info will be updated.
            updated_fields (dict): Keys and updated values to change; allowed keys are 'name', 'date_of_birth', 
                                   'demographics', and 'contact_information'.
            updated_by (str): user_id of the authorized user performing the update (for auditing constraint).

        Returns:
            dict: {
                "success": True,
                "message": "Patient info updated."
            }
            or
            {
                "success": False,
                "error": "Reason for failure"
            }

        Constraints:
            - patient_id must correspond to an existing patient.
            - Only fields: name, date_of_birth, demographics, contact_information may be updated.
            - updated_by must exist as an AuthorizedUser.
            - Standard field structure must be preserved.
            - Audit constraint is fulfilled by requiring updated_by (no audit log in patient itself).

        """
        # Check user exists
        if updated_by not in self.authorized_users:
            return {"success": False, "error": "Authorized user does not exist"}
        # Check patient exists
        if patient_id not in self.patients:
            return {"success": False, "error": "Patient does not exist"}

        allowed_fields = {"name", "date_of_birth", "demographics", "contact_information"}
        invalid_fields = [field for field in updated_fields if field not in allowed_fields]
        if invalid_fields:
            return {
                "success": False,
                "error": f"Invalid field(s) for update: {', '.join(invalid_fields)}"
            }

        # Perform update
        for field, value in updated_fields.items():
            self.patients[patient_id][field] = value
        # Optionally, in production, add audit trail; here, just requiring updated_by parameter

        return {"success": True, "message": "Patient info updated."}

    def add_clinical_encounter(
        self,
        encounter_id: str,
        patient_id: str,
        encounter_type: str,
        date: str,
        attending_provider: str
    ) -> dict:
        """
        Adds a new ClinicalEncounter to the patient's record.

        Args:
            encounter_id (str): Unique identifier for the clinical encounter.
            patient_id (str): The patient's unique ID (must exist).
            encounter_type (str): Type of the clinical encounter (e.g., 'admission', 'consult').
            date (str): Date of the encounter.
            attending_provider (str): Attending provider's identifier or name.

        Returns:
            dict:
                On success: {'success': True, 'message': 'Clinical encounter <encounter_id> added.'}
                On failure: {'success': False, 'error': '<reason>'}
    
        Constraints:
            - encounter_id must be unique in the system.
            - patient_id must exist.
            - All fields must be non-empty.
        """
        # Check for required fields (not None or empty)
        if not all([encounter_id, patient_id, encounter_type, date, attending_provider]):
            return {"success": False, "error": "All fields are required and must be non-empty."}

        # Check encounter_id uniqueness
        if encounter_id in self.clinical_encounters:
            return {"success": False, "error": f"Clinical encounter ID '{encounter_id}' already exists."}

        # Check if patient_id exists
        if patient_id not in self.patients:
            return {"success": False, "error": f"Patient ID '{patient_id}' does not exist."}
    
        new_encounter = {
            "encounter_id": encounter_id,
            "patient_id": patient_id,
            "encounter_type": encounter_type,
            "date": date,
            "attending_provider": attending_provider
        }
        self.clinical_encounters[encounter_id] = new_encounter
        return {"success": True, "message": f"Clinical encounter '{encounter_id}' added."}

    def create_authorized_user(self, user_id: str, name: str, role: str, access_level: str) -> dict:
        """
        Add a new user to the AuthorizedUser registry.

        Args:
            user_id (str): Unique identifier for the user (must not already exist).
            name (str): Name of the user.
            role (str): User's role in the hospital.
            access_level (str): Level of access for the user.

        Returns:
            dict: {
                "success": True,
                "message": "Authorized user <user_id> created."
            } or
            {
                "success": False,
                "error": "User ID already exists."
            }

        Constraints:
            - user_id must be unique (not already registered).
        """
        if user_id in self.authorized_users:
            return { "success": False, "error": "User ID already exists." }

        user_info: AuthorizedUserInfo = {
            "user_id": user_id,
            "name": name,
            "role": role,
            "access_level": access_level
        }
        self.authorized_users[user_id] = user_info
        return { "success": True, "message": f"Authorized user {user_id} created." }

    def update_authorized_user(
        self, 
        user_id: str, 
        name: str = None, 
        role: str = None, 
        access_level: str = None
    ) -> dict:
        """
        Update fields (name, role, access_level) of an authorized user.

        Args:
            user_id (str): The unique identifier of the user to update.
            name (str, optional): The new name for the user.
            role (str, optional): The new role for the user.
            access_level (str, optional): The new access level for the user.

        Returns:
            dict: {
                "success": True,
                "message": "Authorized user updated"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - user_id must exist in the system.
            - At least one of name, role, or access_level must be provided.
            - Common access_level values used by this environment include "restricted", "elevated", "clinical_editor", "doctor", "nurse", "write", and "admin".
        """
        if user_id not in self.authorized_users:
            return { "success": False, "error": "User does not exist" }

        if name is None and role is None and access_level is None:
            return { "success": False, "error": "No update fields provided" }

        user = self.authorized_users[user_id]
        updated_fields = []

        # Only update provided fields.
        if name is not None:
            user["name"] = name
            updated_fields.append("name")
        if role is not None:
            user["role"] = role
            updated_fields.append("role")
        if access_level is not None:
            user["access_level"] = access_level
            updated_fields.append("access_level")

        self.authorized_users[user_id] = user  # Save changes (dict mutation, but for completeness).

        return { "success": True, "message": f"Authorized user updated: {', '.join(updated_fields)}" }

    def delete_authorized_user(self, user_id: str, performed_by_user_id: str) -> dict:
        """
        Remove an authorized user from the system (admin-level action).
    
        Args:
            user_id (str): ID of the user to be deleted.
            performed_by_user_id (str): ID of the user performing the delete operation (must be admin).
    
        Returns:
            dict:
                On success: { "success": True, "message": "Authorized user <user_id> deleted" }
                On failure: { "success": False, "error": "<reason>" }
    
        Constraints:
            - Only users with 'admin' access_level can perform this operation.
            - PatientStatusEntry audit trails ('updated_by') remain untouched.
            - If user_id does not exist, fail gracefully.
        """
        # Check if the user performing the operation exists
        performer = self.authorized_users.get(performed_by_user_id)
        if performer is None:
            return { "success": False, "error": "Performing user does not exist" }
        if performer["access_level"].lower() != "admin":
            return { "success": False, "error": "Permission denied: admin access required" }
    
        # Check if the user to delete exists
        if user_id not in self.authorized_users:
            return { "success": False, "error": "User to delete does not exist" }

        # Proceed to delete the authorized user
        del self.authorized_users[user_id]

        return {
            "success": True,
            "message": f"Authorized user {user_id} deleted"
        }


class HospitalEHRSystem(BaseEnv):
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

    def get_patient_by_id(self, **kwargs):
        return self._call_inner_tool('get_patient_by_id', kwargs)

    def list_all_patients(self, **kwargs):
        return self._call_inner_tool('list_all_patients', kwargs)

    def get_patient_status_history(self, **kwargs):
        return self._call_inner_tool('get_patient_status_history', kwargs)

    def get_latest_patient_status(self, **kwargs):
        return self._call_inner_tool('get_latest_patient_status', kwargs)

    def get_clinical_encounters_by_patient(self, **kwargs):
        return self._call_inner_tool('get_clinical_encounters_by_patient', kwargs)

    def get_status_entry_by_id(self, **kwargs):
        return self._call_inner_tool('get_status_entry_by_id', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def list_authorized_users(self, **kwargs):
        return self._call_inner_tool('list_authorized_users', kwargs)

    def check_user_access_level(self, **kwargs):
        return self._call_inner_tool('check_user_access_level', kwargs)

    def is_patient_id_unique(self, **kwargs):
        return self._call_inner_tool('is_patient_id_unique', kwargs)

    def add_patient_status_entry(self, **kwargs):
        return self._call_inner_tool('add_patient_status_entry', kwargs)

    def update_patient_status_entry(self, **kwargs):
        return self._call_inner_tool('update_patient_status_entry', kwargs)

    def delete_patient_status_entry(self, **kwargs):
        return self._call_inner_tool('delete_patient_status_entry', kwargs)

    def create_patient(self, **kwargs):
        return self._call_inner_tool('create_patient', kwargs)

    def edit_patient_info(self, **kwargs):
        return self._call_inner_tool('edit_patient_info', kwargs)

    def add_clinical_encounter(self, **kwargs):
        return self._call_inner_tool('add_clinical_encounter', kwargs)

    def create_authorized_user(self, **kwargs):
        return self._call_inner_tool('create_authorized_user', kwargs)

    def update_authorized_user(self, **kwargs):
        return self._call_inner_tool('update_authorized_user', kwargs)

    def delete_authorized_user(self, **kwargs):
        return self._call_inner_tool('delete_authorized_user', kwargs)
