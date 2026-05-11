# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict



class PatientInfo(TypedDict):
    patient_id: str
    name: str
    date_of_birth: str  # ISO format recommended
    gender: str
    contact_info: str

class VaccineInfo(TypedDict):
    vaccine_id: str
    vaccine_name: str
    manufacturer: str
    recommended_dosage: str
    type: str  # vaccine type

class ImmunizationEventInfo(TypedDict):
    event_id: str
    patient_id: str
    vaccine_id: str
    date_administered: str  # ISO format recommended
    batch_number: str
    administering_clinician: str
    location: str
    notes: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Patients: {patient_id: PatientInfo}
        self.patients: Dict[str, PatientInfo] = {}
        # Vaccines: {vaccine_id: VaccineInfo}
        self.vaccines: Dict[str, VaccineInfo] = {}
        # Immunization Events: {event_id: ImmunizationEventInfo}
        self.immunization_events: Dict[str, ImmunizationEventInfo] = {}

        # Constraints:
        # - Each ImmunizationEvent must reference a valid Patient and Vaccine.
        # - Deletion of ImmunizationEvent must not violate audit or legal retention policies (e.g., immutable audit log if required).
        # - Only authorized users can modify or delete immunization records.
        # - Patient or Vaccine entries cannot be deleted if referenced by existing ImmunizationEvent records.

    def get_patient_by_name(self, name: str) -> dict:
        """
        Retrieve all patient records that match the given name.

        Args:
            name (str): The full name to look up.

        Returns:
            dict: {
                "success": True,
                "data": List[PatientInfo]  # All patients with matching name (may be empty)
            }

        Notes:
            - Returns all matching patients; names are not unique.
            - No error if no patient found: data = [].
        """
        matches = [
            patient_info for patient_info in self.patients.values()
            if patient_info["name"] == name
        ]
        return { "success": True, "data": matches }

    def get_patient_by_id(self, patient_id: str) -> dict:
        """
        Retrieve patient information by their unique patient_id.

        Args:
            patient_id (str): The unique identifier of the patient.

        Returns:
            dict: 
                On success: {"success": True, "data": PatientInfo}
                On failure: {"success": False, "error": str}
        """
        patient = self.patients.get(patient_id)
        if not patient:
            return {"success": False, "error": "Patient not found"}
        return {"success": True, "data": patient}

    def list_all_patients(self) -> dict:
        """
        List all patients stored in the immunization record system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[PatientInfo]  # List of all patients; may be empty if none.
            }

        Constraints:
            - No special constraints. All patients in the system are listed.
        """
        data = list(self.patients.values())
        return { "success": True, "data": data }

    def get_vaccine_by_name(self, vaccine_name: str) -> dict:
        """
        Retrieve vaccine details using the vaccine_name.

        Args:
            vaccine_name (str): The vaccine name to search for.

        Returns:
            dict:
                On success:
                    { "success": True, "data": VaccineInfo }
                On failure (not found):
                    { "success": False, "error": "Vaccine not found" }
                On invalid input:
                    { "success": False, "error": str }
    
        Constraints:
            - Vaccine name comparison is case-sensitive.
            - Returns the first matching vaccine found if multiple exist.
        """
        if not isinstance(vaccine_name, str) or not vaccine_name:
            return { "success": False, "error": "Invalid vaccine_name provided" }

        for vaccine in self.vaccines.values():
            if vaccine["vaccine_name"] == vaccine_name:
                return { "success": True, "data": vaccine }
    
        return { "success": False, "error": "Vaccine not found" }

    def get_vaccine_by_id(self, vaccine_id: str) -> dict:
        """
        Retrieve information on a vaccine by its vaccine_id.

        Args:
            vaccine_id (str): The ID of the vaccine to retrieve.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": VaccineInfo,  # Vaccine metadata dictionary
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Vaccine not found"
                    }

        Constraints:
            - vaccine_id must exist in the system.
        """
        if not isinstance(vaccine_id, str) or vaccine_id not in self.vaccines:
            return { "success": False, "error": "Vaccine not found" }
        return { "success": True, "data": self.vaccines[vaccine_id] }

    def list_all_vaccines(self) -> dict:
        """
        List all available vaccine records in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[VaccineInfo]  # A list of all vaccine entries (possibly empty)
            }

        This operation has no constraints or error cases: it always succeeds.
        """
        return { "success": True, "data": list(self.vaccines.values()) }

    def list_immunization_events_by_patient(self, patient_id: str) -> dict:
        """
        List all immunization events for the specified patient.

        Args:
            patient_id (str): The ID of the patient.

        Returns:
            dict:
                success: True and data (list of ImmunizationEventInfo) if the patient exists,
                         list will be empty if the patient has no events.
                success: False and error message if the patient does not exist.

        Constraints:
            - Patient must exist in the system.
        """
        if patient_id not in self.patients:
            return { "success": False, "error": "Patient not found" }

        result = [
            event for event in self.immunization_events.values()
            if event["patient_id"] == patient_id
        ]
        return { "success": True, "data": result }

    def get_immunization_event_by_id(self, event_id: str) -> dict:
        """
        Retrieve the full details of an immunization event using its unique event ID.

        Args:
            event_id (str): Unique identifier for the immunization event.

        Returns:
            dict: {
                "success": True,
                "data": ImmunizationEventInfo
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. event not found
            }

        Constraints:
            - The referenced event_id must exist in the system.
        """
        if event_id not in self.immunization_events:
            return { "success": False, "error": "Immunization event not found" }

        event_info = self.immunization_events[event_id]
        return { "success": True, "data": event_info }

    def list_immunization_events_by_vaccine(self, vaccine_id: str) -> dict:
        """
        List all immunization events for a specific vaccine.

        Args:
            vaccine_id (str): The unique identifier of the vaccine to query.

        Returns:
            dict: {
                "success": True,
                "data": List[ImmunizationEventInfo]
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., vaccine not found)
            }

        Constraints:
            - The vaccine_id must exist in the system.
        """
        if vaccine_id not in self.vaccines:
            return { "success": False, "error": "Vaccine not found" }

        event_list = [
            event for event in self.immunization_events.values()
            if event["vaccine_id"] == vaccine_id
        ]
        return { "success": True, "data": event_list }

    def check_patient_references(self, patient_id: str) -> dict:
        """
        Check if a patient is referenced by any ImmunizationEvent records.

        Args:
            patient_id (str): The unique identifier of the patient.

        Returns:
            dict:
                {
                    "success": True,
                    "referenced": bool,  # True if referenced by any ImmunizationEvent, False otherwise
                    "referencing_event_ids": List[str],  # List of event_ids referencing the patient
                }
                OR
                {
                    "success": False,
                    "error": str  # e.g., "Patient does not exist"
                }

        Constraints:
            - Patient must exist.
            - Does not perform any deletion; only reports references.
        """
        if patient_id not in self.patients:
            return { "success": False, "error": "Patient does not exist" }
    
        referencing_event_ids = [
            event_id for event_id, event in self.immunization_events.items()
            if event.get("patient_id") == patient_id
        ]
        return {
            "success": True,
            "referenced": len(referencing_event_ids) > 0,
            "referencing_event_ids": referencing_event_ids
        }

    def check_vaccine_references(self, vaccine_id: str) -> dict:
        """
        Check if a vaccine is referenced by any ImmunizationEvent records.

        Args:
            vaccine_id (str): The unique identifier of the vaccine to check.

        Returns:
            dict: {
                "success": True,
                "referenced": bool  # True if referenced by any event, False otherwise
            }
            or
            {
                "success": False,
                "error": str  # If the vaccine does not exist
            }

        Constraints:
            - Vaccine must exist in the records.
        """
        if vaccine_id not in self.vaccines:
            return { "success": False, "error": "Vaccine does not exist" }

        referenced = any(
            event["vaccine_id"] == vaccine_id
            for event in self.immunization_events.values()
        )

        return { "success": True, "referenced": referenced }

    def can_delete_immunization_event(self, event_id: str, user: str) -> dict:
        """
        Check whether deletion of an immunization event with event_id is permitted for the given user,
        according to retention/audit policies and user authorization.

        Args:
            event_id (str): The ID of the immunization event to check.
            user (str): The user requesting to perform the deletion.

        Returns:
            dict:
                - success (bool): Whether the check was performed successfully.
                - can_delete (bool): If success and permitted, True; otherwise not present.
                - message (str): Info message for success.
                - error (str): Error message if not allowed.

        Constraints:
            - Event must exist.
            - User must be authorized (assumed: user == 'admin' is authorized; can be expanded).
            - Audit/retention policies must allow deletion (assumed allowed for this implementation).
        """
        # Check if event exists
        if event_id not in self.immunization_events:
            return { "success": False, "error": "Immunization event not found" }

        # Check authorization (for simplicity, only 'admin' is authorized)
        # This can be extended to more complex user roles/groups in the future.
        if user != "admin":
            return { "success": False, "error": "User not authorized to delete immunization records" }

        # Simulate audit/retention policy check (no immutable audit log in this schema)
        # If required, this could be based on event properties or system policy.
        # For this implementation, we assume deletion is allowed.
        return {
            "success": True,
            "can_delete": True,
            "message": "Deletion permitted"
        }

    def add_immunization_event(
        self,
        event_id: str,
        patient_id: str,
        vaccine_id: str,
        date_administered: str,
        batch_number: str,
        administering_clinician: str,
        location: str,
        notes: str
    ) -> dict:
        """
        Add a new immunization event (record administration of a vaccine to a patient).

        Args:
            event_id (str): Unique event identifier.
            patient_id (str): ID of the patient who received the vaccine.
            vaccine_id (str): ID of the vaccine administered.
            date_administered (str): Date/time of administration (ISO format recommended).
            batch_number (str): Batch/lot number of the vaccine dose.
            administering_clinician (str): Name or ID of clinician.
            location (str): Administration site location.
            notes (str): Additional notes.

        Returns:
            dict:
                {"success": True, "message": "..."} on success,
                {"success": False, "error": "..."} on validation error.

        Constraints:
            - event_id must be unique (not in system).
            - patient_id must reference an existing patient.
            - vaccine_id must reference an existing vaccine.
        """
        if event_id in self.immunization_events:
            return {"success": False, "error": f"Immunization event with id {event_id} already exists."}
        if patient_id not in self.patients:
            return {"success": False, "error": f"Patient with id {patient_id} does not exist."}
        if vaccine_id not in self.vaccines:
            return {"success": False, "error": f"Vaccine with id {vaccine_id} does not exist."}

        self.immunization_events[event_id] = {
            "event_id": event_id,
            "patient_id": patient_id,
            "vaccine_id": vaccine_id,
            "date_administered": date_administered,
            "batch_number": batch_number,
            "administering_clinician": administering_clinician,
            "location": location,
            "notes": notes
        }
        return {"success": True, "message": f"Immunization event {event_id} added."}

    def update_immunization_event(
        self,
        event_id: str,
        updates: dict,
        authorized: bool = True
    ) -> dict:
        """
        Edit allowed details of an existing immunization event.

        Args:
            event_id (str): The immunization event to update.
            updates (dict): Dict of fields/values to update. Allowed fields include:
                'patient_id', 'vaccine_id', 'date_administered', 'batch_number',
                'administering_clinician', 'location', 'notes'.
            authorized (bool, optional): Must be True for modification to proceed.

        Returns:
            dict: On success: { "success": True, "message": <...> }
                  On error:   { "success": False, "error": <reason> }

        Constraints:
            - Only authorized users can modify events.
            - The event must exist.
            - If patient_id or vaccine_id are updated, the new references must exist.
            - Only recognized fields can be updated.

        """
        # Authorization check
        if not authorized:
            return { "success": False, "error": "User not authorized to modify immunization events." }
        # Existence check
        if event_id not in self.immunization_events:
            return { "success": False, "error": "Immunization event not found." }
        # Allowed fields
        allowed_fields = {
            "patient_id",
            "vaccine_id",
            "date_administered",
            "batch_number",
            "administering_clinician",
            "location",
            "notes"
        }
        # Check for invalid fields
        for key in updates:
            if key not in allowed_fields:
                return { "success": False, "error": f"Field '{key}' cannot be updated or does not exist." }
    
        # Handle referential integrity if patient_id or vaccine_id changed
        if "patient_id" in updates:
            new_pid = updates["patient_id"]
            if new_pid not in self.patients:
                return { "success": False, "error": "Referenced patient_id does not exist." }
        if "vaccine_id" in updates:
            new_vid = updates["vaccine_id"]
            if new_vid not in self.vaccines:
                return { "success": False, "error": "Referenced vaccine_id does not exist." }
        # Perform update
        event = self.immunization_events[event_id]
        for key, value in updates.items():
            event[key] = value
        # Save the changes
        self.immunization_events[event_id] = event
        return { "success": True, "message": "Immunization event updated successfully." }

    def delete_immunization_event(self, event_id: str, user_role: str) -> dict:
        """
        Delete an ImmunizationEvent from the system, subject to constraints:
        - Only authorized users (e.g., roles: 'admin', 'clinician') can delete.
        - If event_id does not exist, returns an error.
        - In a production system, audit/log retention means a true delete should not remove all history;
          here, deletion removes from the active records only.

        Args:
            event_id (str): The unique identifier for the immunization event to be deleted.
            user_role (str): The role of the user performing this operation (authorization).

        Returns:
            dict:
                { "success": True, "message": "Immunization event deleted successfully" }
                or
                { "success": False, "error": <str> }
        """
        # Authorization check
        if user_role not in ['admin', 'clinician']:
            return { "success": False, "error": "Permission denied: unauthorized user role" }

        # Existence check
        if event_id not in self.immunization_events:
            return { "success": False, "error": "Immunization event not found" }

        # In a true production/audit safe system, deletion would likely write to an audit log or mark as deleted
        # For simplicity here, we do a hard delete (removal from dict)
        del self.immunization_events[event_id]

        return { "success": True, "message": "Immunization event deleted successfully" }

    def add_patient(
        self,
        patient_id: str,
        name: str,
        date_of_birth: str,
        gender: str,
        contact_info: str
    ) -> dict:
        """
        Register a new patient in the system.

        Args:
            patient_id (str): Unique identifier for the patient.
            name (str): Patient's name.
            date_of_birth (str): Date of birth (ISO formatted recommended).
            gender (str): Patient's gender.
            contact_info (str): Contact information.

        Returns:
            dict:
                On success: { "success": True, "message": "Patient added successfully." }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - patient_id must be unique (not already present).
            - All fields must be non-empty strings.
        """
        # Basic validation
        if not all([patient_id, name, date_of_birth, gender, contact_info]):
            return { "success": False, "error": "All patient fields must be provided and non-empty." }
        if patient_id in self.patients:
            return { "success": False, "error": "Patient with this ID already exists." }

        self.patients[patient_id] = {
            "patient_id": patient_id,
            "name": name,
            "date_of_birth": date_of_birth,
            "gender": gender,
            "contact_info": contact_info
        }

        return { "success": True, "message": "Patient added successfully." }

    def update_patient_info(
        self,
        patient_id: str,
        name: str = None,
        date_of_birth: str = None,
        gender: str = None,
        contact_info: str = None
    ) -> dict:
        """
        Edit a patient's demographic or contact information.

        Args:
            patient_id (str): Unique ID of the patient to update.
            name (str, optional): Updated patient name.
            date_of_birth (str, optional): Updated date of birth (ISO format recommended).
            gender (str, optional): Updated gender.
            contact_info (str, optional): Updated contact information.

        Returns:
            dict:
                On success: { "success": True, "message": "Patient information updated successfully." }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - The patient must exist.
            - At least one field to update must be provided.
            - Only demographic and contact-info fields may be updated.
        """
        if patient_id not in self.patients:
            return { "success": False, "error": "Patient not found" }
    
        update_fields = {}
        if name is not None:
            update_fields["name"] = name
        if date_of_birth is not None:
            update_fields["date_of_birth"] = date_of_birth
        if gender is not None:
            update_fields["gender"] = gender
        if contact_info is not None:
            update_fields["contact_info"] = contact_info

        if not update_fields:
            return { "success": False, "error": "No update fields specified." }

        # Apply updates
        patient_info = self.patients[patient_id]
        for field, value in update_fields.items():
            patient_info[field] = value

        return { "success": True, "message": "Patient information updated successfully." }

    def delete_patient(self, patient_id: str) -> dict:
        """
        Remove a patient from the system, only if not referenced by any immunization event.

        Args:
            patient_id (str): The unique identifier for the patient to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Patient <id> deleted successfully"
            }
            or
            {
                "success": False,
                "error": "<reason for failure>"
            }

        Constraints:
            - The patient must exist.
            - The patient must not be referenced by any ImmunizationEvent in the system.
            - Does not remove any associated events, nor does it bypass retention checks.
        """
        if patient_id not in self.patients:
            return { "success": False, "error": "Patient not found" }

        # Check if patient is referenced in any ImmunizationEvent
        for event in self.immunization_events.values():
            if event["patient_id"] == patient_id:
                return {
                    "success": False,
                    "error": "Patient cannot be deleted; referenced by immunization events"
                }
        # If no references, safe to delete
        del self.patients[patient_id]
        return {
            "success": True,
            "message": f"Patient {patient_id} deleted successfully"
        }

    def add_vaccine(
        self, 
        vaccine_id: str, 
        vaccine_name: str, 
        manufacturer: str, 
        recommended_dosage: str, 
        type: str
    ) -> dict:
        """
        Add a new vaccine record to the system.

        Args:
            vaccine_id (str): Unique identifier for the vaccine.
            vaccine_name (str): Name of the vaccine.
            manufacturer (str): Manufacturer of the vaccine.
            recommended_dosage (str): Recommended dosage details.
            type (str): The vaccine's category/type.
    
        Returns:
            dict: 
                On success: { "success": True, "message": "Vaccine record added successfully." }
                On failure: { "success": False, "error": <error reason> }

        Constraints:
            - vaccine_id must be unique (must not already exist in the system).
        """
        if not all([vaccine_id, vaccine_name, manufacturer, recommended_dosage, type]):
            return {"success": False, "error": "All vaccine fields must be provided and non-empty."}

        if vaccine_id in self.vaccines:
            return {"success": False, "error": "A vaccine with this vaccine_id already exists."}

        vaccine_info: VaccineInfo = {
            "vaccine_id": vaccine_id,
            "vaccine_name": vaccine_name,
            "manufacturer": manufacturer,
            "recommended_dosage": recommended_dosage,
            "type": type
        }

        self.vaccines[vaccine_id] = vaccine_info
        return {"success": True, "message": "Vaccine record added successfully."}

    def update_vaccine_info(self, vaccine_id: str, update_fields: dict) -> dict:
        """
        Edit vaccine details for a given vaccine.

        Args:
            vaccine_id (str): The unique ID of the vaccine to modify.
            update_fields (dict): Dictionary of fields to update with their new values.
                Valid keys: 'vaccine_name', 'manufacturer', 'recommended_dosage', 'type'

        Returns:
            dict:
                On success:
                    {"success": True, "message": "Vaccine information updated successfully."}
                On failure:
                    {"success": False, "error": <reason>}
        Constraints:
            - Vaccine must exist.
            - Only editable fields are affected.
            - Only authorized users can modify vaccines (assumed permitted).
            - At least one field must be updated.
        """
        # Ensure vaccine exists
        if vaccine_id not in self.vaccines:
            return {"success": False, "error": "Vaccine not found."}

        allowed_fields = {'vaccine_name', 'manufacturer', 'recommended_dosage', 'type'}
        updated = False
        for key, val in update_fields.items():
            if key in allowed_fields:
                self.vaccines[vaccine_id][key] = val
                updated = True
        if not updated:
            return {"success": False, "error": "No valid fields to update."}

        return {"success": True, "message": "Vaccine information updated successfully."}

    def delete_vaccine(self, vaccine_id: str) -> dict:
        """
        Delete a vaccine from the system, only if it is not referenced by any immunization event.

        Args:
            vaccine_id (str): The unique identifier of the vaccine to be deleted.

        Returns:
            dict:
                On success:
                    {"success": True, "message": "Vaccine deleted."}
                On error:
                    {"success": False, "error": <reason>}
        Constraints:
            - Vaccine cannot be deleted if referenced by any ImmunizationEvent.
            - If the vaccine does not exist, operation fails.
        """
        if vaccine_id not in self.vaccines:
            return {"success": False, "error": "Vaccine does not exist."}
    
        # Check if any immunization event references this vaccine
        for event in self.immunization_events.values():
            if event["vaccine_id"] == vaccine_id:
                return {
                    "success": False,
                    "error": "Vaccine is referenced by existing immunization events and cannot be deleted."
                }
    
        # If not referenced, delete
        del self.vaccines[vaccine_id]
        return {"success": True, "message": "Vaccine deleted."}


class ElectronicImmunizationRecordManagementSystem(BaseEnv):
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

    def get_vaccine_by_name(self, **kwargs):
        return self._call_inner_tool('get_vaccine_by_name', kwargs)

    def get_vaccine_by_id(self, **kwargs):
        return self._call_inner_tool('get_vaccine_by_id', kwargs)

    def list_all_vaccines(self, **kwargs):
        return self._call_inner_tool('list_all_vaccines', kwargs)

    def list_immunization_events_by_patient(self, **kwargs):
        return self._call_inner_tool('list_immunization_events_by_patient', kwargs)

    def get_immunization_event_by_id(self, **kwargs):
        return self._call_inner_tool('get_immunization_event_by_id', kwargs)

    def list_immunization_events_by_vaccine(self, **kwargs):
        return self._call_inner_tool('list_immunization_events_by_vaccine', kwargs)

    def check_patient_references(self, **kwargs):
        return self._call_inner_tool('check_patient_references', kwargs)

    def check_vaccine_references(self, **kwargs):
        return self._call_inner_tool('check_vaccine_references', kwargs)

    def can_delete_immunization_event(self, **kwargs):
        return self._call_inner_tool('can_delete_immunization_event', kwargs)

    def add_immunization_event(self, **kwargs):
        return self._call_inner_tool('add_immunization_event', kwargs)

    def update_immunization_event(self, **kwargs):
        return self._call_inner_tool('update_immunization_event', kwargs)

    def delete_immunization_event(self, **kwargs):
        return self._call_inner_tool('delete_immunization_event', kwargs)

    def add_patient(self, **kwargs):
        return self._call_inner_tool('add_patient', kwargs)

    def update_patient_info(self, **kwargs):
        return self._call_inner_tool('update_patient_info', kwargs)

    def delete_patient(self, **kwargs):
        return self._call_inner_tool('delete_patient', kwargs)

    def add_vaccine(self, **kwargs):
        return self._call_inner_tool('add_vaccine', kwargs)

    def update_vaccine_info(self, **kwargs):
        return self._call_inner_tool('update_vaccine_info', kwargs)

    def delete_vaccine(self, **kwargs):
        return self._call_inner_tool('delete_vaccine', kwargs)

