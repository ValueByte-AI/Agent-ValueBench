# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import json
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
from datetime import datetime
from typing import List, Dict, Any
import uuid
import time



class PatientInfo(TypedDict):
    patient_id: str
    name: str
    date_of_birth: str
    contact_information: str
    authentication_credential: str

class MedicalTestResultInfo(TypedDict):
    result_id: str
    patient_id: str
    test_type: str
    result_value: float
    result_units: str
    result_date: str
    ordering_provider: str
    notes: str

class VisitSummaryInfo(TypedDict):
    visit_id: str
    patient_id: str
    provider_id: str
    visit_date: str
    notes: str
    diagnosis: str

class ProviderInfo(TypedDict):
    provider_id: str
    name: str
    specialization: str
    contact_information: str

class MessageInfo(TypedDict):
    message_id: str
    sender_id: str
    receiver_id: str
    patient_id: str
    timestamp: str
    content: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Patient portal stateful environment for electronic health records.
        """

        # Patients: {patient_id: PatientInfo}
        self.patients: Dict[str, PatientInfo] = {}

        # Medical Test Results: {result_id: MedicalTestResultInfo}
        self.medical_test_results: Dict[str, MedicalTestResultInfo] = {}

        # Visit Summaries: {visit_id: VisitSummaryInfo}
        self.visit_summaries: Dict[str, VisitSummaryInfo] = {}

        # Healthcare Providers: {provider_id: ProviderInfo}
        self.providers: Dict[str, ProviderInfo] = {}

        # Messages: {message_id: MessageInfo}
        self.messages: Dict[str, MessageInfo] = {}

        # --- Constraints (as comments) ---
        # - Each medical test result must be associated with a valid patient.
        # - Patients can only access their own records and communications.
        # - Test results must be timestamped and filterable by date.
        # - Communications are visible only to authorized participants.
        # - Data integrity and auditability must be preserved for all access and modifications.

    @staticmethod
    def _is_admin_user(user_id: str) -> bool:
        if not isinstance(user_id, str):
            return False
        normalized = user_id.strip().lower()
        return normalized == "admin" or normalized.startswith("admin-") or normalized.startswith("admin_")

    def _resolve_actor_type(self, user_id: str) -> str | None:
        if user_id in self.patients:
            return "patient"
        if user_id in self.providers:
            if self._is_admin_user(user_id):
                return "admin"
            return "provider"
        if self._is_admin_user(user_id):
            return "admin"
        return None

    def get_patient_by_id(self, patient_id: str) -> dict:
        """
        Retrieve patient information by patient_id.
    
        Args:
            patient_id (str): The unique identifier of the patient.
    
        Returns:
            dict: {
                "success": True,
                "data": PatientInfo  # Patient's info dict
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., patient not found)
            }
    
        Constraints:
            - patient_id must exist in the system.
            - Access control for actual authorization is handled elsewhere.
        """
        patient = self.patients.get(patient_id)
        if patient is None:
            return { "success": False, "error": "Patient not found" }
        return { "success": True, "data": patient }

    def get_patient_by_auth(self, authentication_credential: str) -> dict:
        """
        Retrieve patient information after verifying authentication credentials.

        Args:
            authentication_credential (str): Credential (e.g., password/token) to identify and authenticate a patient.

        Returns:
            dict:
                - success: True and data: PatientInfo if the credential matches exactly one patient.
                - success: False and error: description if invalid or ambiguous credential.
        Constraints:
            - Only the patient's own record is accessible via their credential.
            - There must be exactly one patient with the given credential.
        """
        matching_patients = [
            patient for patient in self.patients.values()
            if patient['authentication_credential'] == authentication_credential
        ]
        if len(matching_patients) == 0:
            return { "success": False, "error": "Invalid authentication." }
        if len(matching_patients) > 1:
            return { "success": False, "error": "Multiple patients found for this credential. Data integrity issue." }
        # Exactly one match
        return { "success": True, "data": matching_patients[0] }

    def list_patient_test_results(self, patient_id: str, requester_id: str) -> dict:
        """
        Get all medical test results associated with a given patient.

        Args:
            patient_id (str): The target patient's unique identifier.
            requester_id (str): The ID of the user requesting the information.
                Patients can review their own results, ordering providers can review
                the results they ordered, and admin users can review the full set.

        Returns:
            dict: {
                "success": True,
                "data": List[MedicalTestResultInfo],  # May be empty list if no results
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (not found or permission denied)
            }
    
        Constraints:
            - Each test result must be associated with a valid patient.
            - Patients may only access their own test results.
            - Ordering providers may review results they ordered for the patient.
            - Admin users may review all of the patient's results.
        """
        # Verify patient existence
        if patient_id not in self.patients:
            return {"success": False, "error": "Patient not found"}
        # Collect all test results for the patient
        results = [
            result for result in self.medical_test_results.values()
            if result["patient_id"] == patient_id
        ]
        # Enforce access control
        if requester_id == patient_id:
            return {"success": True, "data": results}
        if self._is_admin_user(requester_id):
            return {"success": True, "data": results}
        if requester_id in self.providers:
            provider_results = [
                result for result in results
                if result.get("ordering_provider") == requester_id
            ]
            if provider_results or not results:
                return {"success": True, "data": provider_results}
            return {"success": False, "error": "Access denied: Provider may only view results they ordered"}
        return {"success": False, "error": "Access denied: Patients may only view their own results"}


    def filter_patient_test_results_by_date(self, patient_id: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Filter a patient's medical test results within a given date range (inclusive).
    
        Args:
            patient_id (str): The ID of the patient for whom test results are requested.
            start_date (str): Start of the date range, format 'YYYY-MM-DD'.
            end_date (str): End of the date range, format 'YYYY-MM-DD'.
        
        Returns:
            dict: {
                "success": True,
                "data": List[MedicalTestResultInfo]  # May be empty if no results in date range
            }
            or
            {
                "success": False,
                "error": str
            }
        Constraints:
            - Only results for the given patient_id will be returned.
            - Dates are inclusive.
            - Returns empty list if none found.
            - Returns error for invalid patient_id or date format, or if start_date > end_date.
        """
        if patient_id not in self.patients:
            return {"success": False, "error": "Patient does not exist"}

        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            return {"success": False, "error": "Invalid date format; use YYYY-MM-DD"}
    
        if start_dt > end_dt:
            return {"success": False, "error": "Start date is after end date"}
    
        results: List[MedicalTestResultInfo] = []
        for result in self.medical_test_results.values():
            if result["patient_id"] != patient_id:
                continue
            try:
                result_dt = datetime.strptime(result["result_date"], "%Y-%m-%d")
            except ValueError:
                continue  # Skip results with invalid date format
            if start_dt <= result_dt <= end_dt:
                results.append(result)
        return {"success": True, "data": results}

    def filter_patient_test_results_by_type(
        self, patient_id: str, test_type: str, requesting_user_id: str
    ) -> dict:
        """
        Filter a patient's medical test results by test type, ensuring only the patient
        can access their own results.

        Args:
            patient_id (str): The patient whose test results to filter.
            test_type (str): The type of test to filter by (exact match).
            requesting_user_id (str): The ID of the user making the request (should match patient_id).

        Returns:
            dict: {
                "success": True,
                "data": List[MedicalTestResultInfo]  # May be empty,
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure.
            }

        Constraints:
            - Only the patient can access their own results.
            - Patient must exist.
        """
        if patient_id not in self.patients:
            return {"success": False, "error": "Patient does not exist."}

        if requesting_user_id != patient_id:
            return {"success": False, "error": "Access denied: patients can only access their own records."}

        filtered_results = [
            result for result in self.medical_test_results.values()
            if result["patient_id"] == patient_id and result["test_type"] == test_type
        ]

        return {"success": True, "data": filtered_results}

    def get_test_result_by_id(self, result_id: str, requesting_patient_id: str = None) -> dict:
        """
        Retrieve a detailed medical test result by its result_id.

        Args:
            result_id (str): The unique identifier for the medical test result.
            requesting_patient_id (str, optional): The patient requesting the result.
                If provided, access control is enforced (patient can only access their own record).

        Returns:
            dict:
                On success:
                    { "success": True, "data": MedicalTestResultInfo }
                On failure:
                    {
                      "success": False,
                      "error": "Medical test result does not exist"
                    }
                    OR
                    {
                      "success": False,
                      "error": "Access denied"
                    }

        Constraints:
            - The medical test result must exist.
            - If requesting_patient_id is provided, patients can only access their own test results.
        """
        mtr = self.medical_test_results.get(result_id)
        if not mtr:
            return { "success": False, "error": "Medical test result does not exist" }

        if requesting_patient_id is not None:
            if mtr["patient_id"] != requesting_patient_id:
                return { "success": False, "error": "Access denied" }

        return { "success": True, "data": mtr }

    def list_patient_visit_summaries(self, patient_id: str, acting_patient_id: str) -> dict:
        """
        Return all visit summaries for a specified patient, enforcing access control.

        Args:
            patient_id (str): ID of the patient whose records to fetch.
            acting_patient_id (str): ID of the patient making the request.

        Returns:
            dict: {
                "success": True,
                "data": List[VisitSummaryInfo]  # Possibly empty
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - patient_id must exist.
            - Only the patient themselves can view their visit summaries.
        """
        if patient_id not in self.patients:
            return {"success": False, "error": "Patient does not exist"}
        if acting_patient_id != patient_id:
            return {"success": False, "error": "Access denied: patients can only access their own records"}
        # List summaries associated with patient_id
        results = [
            vs for vs in self.visit_summaries.values()
            if vs["patient_id"] == patient_id
        ]
        return {"success": True, "data": results}

    def filter_patient_visit_summaries_by_date(
        self,
        patient_id: str,
        start_date: str,
        end_date: str
    ) -> dict:
        """
        Return all visit summaries for a given patient within a specific date range (inclusive).

        Args:
            patient_id (str): The patient whose visit summaries to filter.
            start_date (str): The beginning of the date range, 'YYYY-MM-DD'.
            end_date (str): The end of the date range, 'YYYY-MM-DD'.

        Returns:
            dict:
              - {"success": True, "data": List[VisitSummaryInfo]} on success, may be empty
              - {"success": False, "error": str} on error (e.g. invalid patient or dates)

        Constraints:
            - patient_id must exist
            - start_date and end_date must be valid and start_date <= end_date (lexical comparison)
            - Only returns records for the given patient
        """
        if patient_id not in self.patients:
            return {"success": False, "error": "Patient does not exist"}
        if start_date > end_date:
            return {"success": False, "error": "start_date must not be after end_date"}

        filtered = [
            vs for vs in self.visit_summaries.values()
            if vs["patient_id"] == patient_id and start_date <= vs["visit_date"] <= end_date
        ]

        return {"success": True, "data": filtered}

    def get_provider_by_id(self, provider_id: str) -> dict:
        """
        Retrieve healthcare provider details by provider_id.

        Args:
            provider_id (str): The unique identifier of the provider.

        Returns:
            dict: {
                "success": True,
                "data": ProviderInfo  # Provider's details as a dictionary
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g., "Provider not found"
            }

        Constraints:
            - Returns details only if provider_id exists in the system.
        """
        provider = self.providers.get(provider_id)
        if provider is None:
            return { "success": False, "error": "Provider not found" }
        return { "success": True, "data": provider }

    def list_providers(self) -> dict:
        """
        List all healthcare providers currently in the system.

        Args:
            None

        Returns:
            dict:
              {
                "success": True,
                "data": List[ProviderInfo]  # List may be empty if no providers exist
              }
        """
        providers_list = list(self.providers.values())
        return { "success": True, "data": providers_list }

    def list_patient_messages(
        self, 
        patient_id: str, 
        requester_id: str, 
        requester_role: str
    ) -> dict:
        """
        Retrieve all messages associated with a patient, with authorization.

        Args:
            patient_id (str): The ID of the patient whose messages are requested.
            requester_id (str): The ID of user making the request (may be a patient,
                provider, or admin).
            requester_role (str): Role of requester: 'patient', 'provider', or 'admin'.

        Returns:
            dict: 
                Success: {"success": True, "data": List[MessageInfo]}
                Failure: {"success": False, "error": str}
    
        Constraints:
            - Only the patient, an authorized provider participant, or an admin may access messages.
            - Patient: Can access only their own participant messages.
            - Provider: Can access only messages where they are sender or receiver with this patient,
              unless the provider account is an administrative account.
            - Admin: Can access all messages linked to the patient.
            - All access must be audited elsewhere.
        """
        # Check if patient exists
        if patient_id not in self.patients:
            return {"success": False, "error": "Patient not found"}

        # Patient access: can only access own messages
        if requester_role == "patient":
            if requester_id != patient_id:
                return {"success": False, "error": "Access denied"}
            result = [
                msg for msg in self.messages.values()
                if msg["patient_id"] == patient_id and
                   (msg["sender_id"] == requester_id or msg["receiver_id"] == requester_id)
            ]
            return {"success": True, "data": result}
    
        # Provider access: must be a sender or receiver of the message
        elif requester_role == "provider":
            if requester_id not in self.providers and not self._is_admin_user(requester_id):
                return {"success": False, "error": "Provider not found"}
            if self._is_admin_user(requester_id):
                result = [
                    msg for msg in self.messages.values()
                    if msg["patient_id"] == patient_id
                ]
                return {"success": True, "data": result}
            result = [
                msg for msg in self.messages.values()
                if msg["patient_id"] == patient_id and 
                   (msg["sender_id"] == requester_id or msg["receiver_id"] == requester_id)
            ]
            return {"success": True, "data": result}
        elif requester_role == "admin":
            if not self._is_admin_user(requester_id):
                return {"success": False, "error": "Admin not found"}
            result = [
                msg for msg in self.messages.values()
                if msg["patient_id"] == patient_id
            ]
            return {"success": True, "data": result}
    
        else:
            return {"success": False, "error": "Invalid requester role"}

    def filter_patient_messages_by_date(self, patient_id: str, start_date: str, end_date: str) -> dict:
        """
        Retrieve all patient-provider messages for a given patient_id, where the message's 
        timestamp falls within the [start_date, end_date] range (inclusive).

        Args:
            patient_id (str): The patient's unique identifier (messages must belong to this patient).
            start_date (str): The start of the date range (inclusive), ISO format 'YYYY-MM-DD'.
            end_date (str): The end of the date range (inclusive), ISO format 'YYYY-MM-DD'.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": List[MessageInfo],  # Messages in date range (empty list if none)
                }
                or
                {
                    "success": False,
                    "error": str  # Reason for failure
                }

        Constraints:
            - Patient must exist.
            - Only messages where message.patient_id == given patient_id are included.
            - Date range must be valid (start_date <= end_date).
        """
        if patient_id not in self.patients:
            return { "success": False, "error": "Patient not found" }

        # Check date logic
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            return { "success": False, "error": "Invalid date format; use YYYY-MM-DD." }

        if start_dt > end_dt:
            return { "success": False, "error": "Invalid date range" }

        matched_messages = []
        for message in self.messages.values():
            if message["patient_id"] != patient_id:
                continue
            # Parse message timestamp to date (assume timestamp is in 'YYYY-MM-DD...' format)
            try:
                msg_dt = datetime.strptime(message["timestamp"][:10], '%Y-%m-%d')
            except ValueError:
                continue  # skip malformed timestamps
            if start_dt <= msg_dt <= end_dt:
                matched_messages.append(message)

        return { "success": True, "data": matched_messages }

    def get_message_by_id(self, message_id: str, requesting_user_id: str) -> dict:
        """
        Retrieve a specific message by message_id, only if the requesting user is an authorized participant.
    
        Args:
            message_id (str): The unique identifier for the message.
            requesting_user_id (str): The user ID making the request (could be a patient or provider).

        Returns:
            dict: 
                Success: { "success": True, "data": MessageInfo }
                Failure: { "success": False, "error": "reason" }

        Constraints:
            - The message must exist.
            - Only the sender, receiver, or linked patient can access the message.
        """
        msg = self.messages.get(message_id)
        if not msg:
            return { "success": False, "error": "Message not found" }

        if (requesting_user_id != msg["sender_id"] and 
            requesting_user_id != msg["receiver_id"] and 
            requesting_user_id != msg["patient_id"]):
            return { "success": False, "error": "Access denied: Not an authorized participant" }

        return { "success": True, "data": msg }

    def check_record_access_rights(
        self,
        user_id: str,
        user_type: str,
        record_type: str,
        record_id: str
    ) -> dict:
        """
        Validate if a patient or provider is authorized to access a record.

        Args:
            user_id (str): The ID of the patient or provider.
            user_type (str): Either "patient" or "provider".
            record_type (str): "medical_test_result", "visit_summary", or "message".
            record_id (str): ID of the specific record.

        Returns:
            dict:
              - On input or lookup error:
                    { "success": False, "error": <error_description> }
              - On success:
                    {
                      "success": True,
                      "authorized": <bool>,
                      "reason": <str>
                    }

        Constraints:
            - Patients can only access their own records (test results, visits, messages).
            - Providers can access records they are responsible for (ordered tests, their visits, messages they're party to).
            - Record must exist.
            - User must exist.
        """
        # Validate user_type
        if user_type not in ("patient", "provider"):
            return { "success": False, "error": "Invalid user type." }

        # Validate user exists
        if user_type == "patient":
            if user_id not in self.patients:
                return { "success": False, "error": "Patient not found." }
        elif user_type == "provider":
            if user_id not in self.providers:
                return { "success": False, "error": "Provider not found." }

        # Fetch and check record existence, then access rights
        if record_type == "medical_test_result":
            recs = self.medical_test_results
            if record_id not in recs:
                return { "success": False, "error": "Medical test result not found." }
            rec = recs[record_id]
            if user_type == "patient":
                authorized = (rec["patient_id"] == user_id)
                reason = "Patient access: " + ("authorized" if authorized else "not this patient's result")
            elif user_type == "provider":
                authorized = (rec["ordering_provider"] == user_id)
                reason = "Provider access: " + ("authorized" if authorized else "not the ordering provider")
            return {"success": True, "authorized": authorized, "reason": reason}

        elif record_type == "visit_summary":
            recs = self.visit_summaries
            if record_id not in recs:
                return { "success": False, "error": "Visit summary not found." }
            rec = recs[record_id]
            if user_type == "patient":
                authorized = (rec["patient_id"] == user_id)
                reason = "Patient access: " + ("authorized" if authorized else "not this patient's visit")
            elif user_type == "provider":
                authorized = (rec["provider_id"] == user_id)
                reason = "Provider access: " + ("authorized" if authorized else "not the provider for this visit")
            return {"success": True, "authorized": authorized, "reason": reason}

        elif record_type == "message":
            recs = self.messages
            if record_id not in recs:
                return { "success": False, "error": "Message not found." }
            rec = recs[record_id]
            if user_type == "patient":
                # Patient can see message if they are the patient, and (sender or receiver of the message)
                authorized = (rec["patient_id"] == user_id) and (rec["sender_id"] == user_id or rec["receiver_id"] == user_id)
                reason = "Patient access: " + ("authorized" if authorized else "not authorized for this message")
            elif user_type == "provider":
                # Provider can access if they're sender or receiver
                authorized = (rec["sender_id"] == user_id or rec["receiver_id"] == user_id)
                reason = "Provider access: " + ("authorized" if authorized else "not a party to this message")
            return {"success": True, "authorized": authorized, "reason": reason}

        else:
            return { "success": False, "error": "Invalid record type." }

    def get_audit_log_for_patient(self, patient_id: str) -> dict:
        """
        Retrieve access/modification audit logs for a patient’s records.

        Args:
            patient_id (str): The ID of the patient whose audit logs are to be retrieved.

        Returns:
            dict: {
                "success": True,
                "data": List[dict],  # audit log entries for the patient (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # description of error
            }

        Constraints:
            - The patient_id must exist.
            - Returns all audit log entries associated with that patient_id.
        """
        # Ensure audit_logs exists; initialize if not present (for robustness in this simulation)
        if not hasattr(self, "audit_logs"):
            self.audit_logs: Dict[str, list] = {}

        # Check for patient existence
        if patient_id not in self.patients:
            return {"success": False, "error": "Patient does not exist"}

        # Retrieve audit logs for the given patient.
        logs = self.audit_logs.get(patient_id, [])
        return {"success": True, "data": logs}

    def add_medical_test_result(
        self,
        result_id: str,
        patient_id: str,
        test_type: str,
        result_value: float,
        result_units: str,
        result_date: str,
        ordering_provider: str,
        notes: str,
        actor_id: str = "system"  # Optionally track who performed the operation
    ) -> dict:
        """
        Add a new medical test result for a patient with integrity validation and audit logging.

        Args:
            result_id (str): Unique identifier for the test result.
            patient_id (str): ID of the patient the test result is associated with.
            test_type (str): Type/name of the test.
            result_value (float): Result numerical value.
            result_units (str): Measurement units for the result.
            result_date (str): Result date (timestamp, ISO format preferred).
            ordering_provider (str): ID of the provider who ordered the test.
            notes (str): Supplementary notes for the test.
            actor_id (str): The ID of the actor performing this operation (for audit).

        Returns:
            dict: {
                "success": True, "message": "Medical test result added for patient <patient_id>."
            }
            or
            dict: {
                "success": False, "error": "<reason>"
            }

        Constraints:
            - Medical test result must have a unique result_id.
            - Test result must be for an existing patient.
            - Audit log captures the creation event.
        """
        # Check patient exists
        if patient_id not in self.patients:
            return {"success": False, "error": f"Patient with ID {patient_id} does not exist."}
    
        # Check result_id uniqueness
        if result_id in self.medical_test_results:
            return {"success": False, "error": f"Test result with ID {result_id} already exists."}
    
        # Minimal type checking for float result_value
        try:
            result_value = float(result_value)
        except Exception:
            return {"success": False, "error": "Invalid result_value: Must be a float."}

        # Create new test result
        new_result: MedicalTestResultInfo = {
            "result_id": result_id,
            "patient_id": patient_id,
            "test_type": test_type,
            "result_value": result_value,
            "result_units": result_units,
            "result_date": result_date,
            "ordering_provider": ordering_provider,
            "notes": notes,
        }
        self.medical_test_results[result_id] = new_result

        # Ensure an audit log exists
        if not hasattr(self, 'audit_log'):
            self.audit_log = []
        self.audit_log.append({
            "event": "add_medical_test_result",
            "result_id": result_id,
            "patient_id": patient_id,
            "actor_id": actor_id,
            "timestamp": result_date,
            "details": {
                "test_type": test_type,
                "ordering_provider": ordering_provider,
            }
        })

        return {
            "success": True,
            "message": f"Medical test result added for patient {patient_id}."
        }

    def update_medical_test_result(
        self, 
        result_id: str, 
        updated_fields: dict, 
        user_id: str
    ) -> dict:
        """
        Update an existing medical test result's details, ensuring audit logging and data integrity.

        Args:
            result_id (str): ID of the medical test result to update.
            updated_fields (dict): Dictionary of updatable fields and their new values.
            user_id (str): ID of the user performing the update (for access logging and permissions).

        Returns:
            dict: {
                "success": True,
                "message": "Medical test result updated and audited."
                }
                or
                {
                "success": False,
                "error": "<reason>"
                }

        Constraints:
            - Only authorized users (e.g. ordering provider or admin) can update a test result.
            - Cannot update result_id or patient_id (integrity).
            - Audit log must record the update (simulate as list self.audit_log).
        """
        # Check result exists
        if result_id not in self.medical_test_results:
            return {"success": False, "error": "Medical test result not found."}
    
        result = self.medical_test_results[result_id]

        # Check authorization: Only provider who ordered OR an admin
        is_ordering_provider = (user_id == result["ordering_provider"])
        is_admin = self._is_admin_user(user_id)
        if not (is_ordering_provider or is_admin):
            return {"success": False, "error": "Permission denied: Not authorized to update this test result."}
    
        # Validate updatable fields: Only allow modification for specific fields except result_id and patient_id
        protected_fields = {"result_id", "patient_id"}
        all_fields = set(result.keys())
        for field in updated_fields:
            if (field not in all_fields) or (field in protected_fields):
                return {"success": False, "error": f"Invalid or immutable field in update: {field}"}
    
        # Perform update
        for field, value in updated_fields.items():
            result[field] = value

        # Simulate an audit log if not existing
        if not hasattr(self, "audit_log"):
            self.audit_log = []

        self.audit_log.append({
            "event": "update_medical_test_result",
            "result_id": result_id,
            "updated_fields": list(updated_fields.keys()),
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
        })

        return {
            "success": True,
            "message": "Medical test result updated and audited."
        }

    def delete_medical_test_result(self, result_id: str, requester_id: str) -> dict:
        """
        Remove a medical test result with integrity and audit logging.

        Args:
            result_id (str): The unique ID of the medical test result to delete.
            requester_id (str): The ID of the entity requesting the deletion (should be the owning patient).

        Returns:
            dict: {
              "success": True,
              "message": "Medical test result <result_id> deleted."
            }
            or
            {
              "success": False,
              "error": <reason>
            }

        Constraints:
          - The result must exist.
          - Only the patient who owns the record can delete it.
          - Deletions must be logged for auditability.
        """
        # Check if the test result exists
        result = self.medical_test_results.get(result_id)
        if not result:
            return { "success": False, "error": "Medical test result does not exist." }
    
        patient_id = result["patient_id"]
        # Verify the corresponding patient exists
        if patient_id not in self.patients:
            return { "success": False, "error": "Associated patient record does not exist." }  # Integrity check

        # Authorization: only the patient themself can delete
        if requester_id != patient_id:
            return { "success": False, "error": "Unauthorized: only the patient may delete their own test results." }

        if hasattr(self, "log_access_event"):
            self.log_access_event(
                user_id=requester_id,
                patient_id=patient_id,
                record_type="medical_test_result",
                record_id=result_id,
                action="deleted",
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
                description="Medical test result deleted by patient."
            )

        # Remove the test result
        del self.medical_test_results[result_id]

        return { "success": True, "message": f"Medical test result {result_id} deleted." }

    def add_visit_summary(
        self,
        visit_id: str,
        patient_id: str,
        provider_id: str,
        visit_date: str,
        notes: str,
        diagnosis: str
    ) -> dict:
        """
        Create and store a new visit summary for a patient.

        Args:
            visit_id (str): Unique ID for the visit summary.
            patient_id (str): Patient's unique identifier (must exist).
            provider_id (str): Provider's unique identifier (must exist).
            visit_date (str): Date of the visit.
            notes (str): Notes from the visit.
            diagnosis (str): Diagnosis from the visit.

        Returns:
            dict:
                On success: { "success": True, "message": "Visit summary added." }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - visit_id must be globally unique.
            - patient_id must correspond to an existing patient.
            - provider_id must correspond to an existing provider.
        """
        # Check for required parameters
        param_map = {
            "visit_id": visit_id, "patient_id": patient_id, "provider_id": provider_id,
            "visit_date": visit_date, "notes": notes, "diagnosis": diagnosis
        }
        for field, value in param_map.items():
            if value is None or str(value).strip() == '':
                return { "success": False, "error": f"Missing required field: {field}" }

        # Ensure visit_id uniqueness
        if visit_id in self.visit_summaries:
            return { "success": False, "error": "Visit ID already exists" }

        # Ensure patient exists
        if patient_id not in self.patients:
            return { "success": False, "error": "Patient does not exist" }

        # Ensure provider exists
        if provider_id not in self.providers:
            return { "success": False, "error": "Provider does not exist" }

        # Compose VisitSummaryInfo entry
        summary: VisitSummaryInfo = VisitSummaryInfo(
            visit_id=visit_id,
            patient_id=patient_id,
            provider_id=provider_id,
            visit_date=visit_date,
            notes=notes,
            diagnosis=diagnosis
        )
        self.visit_summaries[visit_id] = summary

        # If audit log feature is present, could trigger here (not in this method for now)

        return { "success": True, "message": "Visit summary added." }

    def update_visit_summary(self, visit_id: str, updates: dict) -> dict:
        """
        Edit an existing visit summary entry.

        Args:
            visit_id (str): The unique identifier of the visit summary to update.
            updates (dict): Dict of fields and new values to update. Valid keys: "visit_date", "notes", "diagnosis", "provider_id", "patient_id".

        Returns:
            dict: 
                - { "success": True, "message": "Visit summary updated successfully." }
                - { "success": False, "error": "Visit summary not found." }
                - { "success": False, "error": "No valid fields to update." }

        Constraints:
            - The visit summary must exist.
            - Cannot modify visit_id.
            - Only allows updating valid fields: "visit_date", "notes", "diagnosis", "provider_id", "patient_id".
        """
        if visit_id not in self.visit_summaries:
            return { "success": False, "error": "Visit summary not found." }

        valid_fields = {"visit_date", "notes", "diagnosis", "provider_id", "patient_id"}
        update_count = 0

        for key, value in updates.items():
            if key in valid_fields:
                self.visit_summaries[visit_id][key] = value
                update_count += 1

        if update_count == 0:
            return { "success": False, "error": "No valid fields to update." }

        return { "success": True, "message": "Visit summary updated successfully." }

    def add_message(
        self,
        sender_id: str,
        receiver_id: str,
        patient_id: str,
        content: str,
        timestamp: str
    ) -> dict:
        """
        Send and store a new message between a patient and provider.

        Args:
            sender_id (str): ID of the sender (a patient or a provider).
            receiver_id (str): ID of the receiver (a provider or a patient).
            patient_id (str): ID of the patient to whom the message pertains.
            content (str): Message content.
            timestamp (str): Timestamp of the message (ideally ISO string).

        Returns:
            dict: {
                "success": True,
                "message": "Message sent and stored successfully."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure.
            }

        Constraints:
            - Only authorized parties (the patient, authorized provider(s), and admin support users)
              can send/receive messages.
            - The patient must exist in the system.
            - Both sender and receiver must exist as supported actor types and be related to the patient
              or to an administrative escalation about the patient.
            - Data integrity: Each message_id must be unique.
        """
        # Validate the patient exists
        if patient_id not in self.patients:
            return {"success": False, "error": "Patient does not exist."}

        # Is sender/receiver a supported actor type?
        sender_type = self._resolve_actor_type(sender_id)
        receiver_type = self._resolve_actor_type(receiver_id)

        if not sender_type:
            return {"success": False, "error": "Sender does not exist."}
        if not receiver_type:
            return {"success": False, "error": "Receiver does not exist."}

        patient_involved = sender_id == patient_id or receiver_id == patient_id
        admin_escalation = (
            (sender_type == "admin" and receiver_type == "provider")
            or (sender_type == "provider" and receiver_type == "admin")
        )

        # Only allow messages where either sender or receiver is the given patient,
        # except for an admin-provider escalation explicitly tied to the patient.
        if not patient_involved and not admin_escalation:
            return {"success": False, "error": "Messages must involve the patient as either sender or receiver."}

        # Optionally: enforce sender and receiver are not the same (skip unless specified)
        if not content or not isinstance(content, str) or content.strip() == "":
            return {"success": False, "error": "Message content cannot be empty."}

        # Generate a unique message_id
        message_id = str(uuid.uuid4())
        while message_id in self.messages:
            message_id = str(uuid.uuid4())

        # Prepare message entry
        msg_info = {
            "message_id": message_id,
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "patient_id": patient_id,
            "timestamp": timestamp,
            "content": content.strip()
        }

        self.messages[message_id] = msg_info

        # Audit trail (could call log_access_event if implemented)
        # Example:
        # if hasattr(self, "log_access_event"):
        #     self.log_access_event(event_type="add_message", actor_id=sender_id, patient_id=patient_id, metadata={"message_id": message_id})

        return {"success": True, "message": "Message sent and stored successfully."}

    def update_patient_contact_information(
        self, patient_id: str, new_contact_information: str, performed_by: str
    ) -> dict:
        """
        Update a patient's contact information and log the change for auditability.

        Args:
            patient_id (str): The ID of the patient whose contact information is to be updated.
            new_contact_information (str): The new contact information string.
            performed_by (str): The user or system ID performing the update (for audit purposes).

        Returns:
            dict: 
                On success:
                    {"success": True, "message": "Contact information updated and change logged."}
                On failure:
                    {"success": False, "error": <error_message>}
        Constraints:
            - Patient must exist in the system.
            - The change must be logged for auditability, including before/after state and actor.
        """

        # Check if patient exists
        if patient_id not in self.patients:
            return {"success": False, "error": "Patient not found."}

        old_contact_info = self.patients[patient_id]["contact_information"]
        self.patients[patient_id]["contact_information"] = new_contact_information

        # Prepare the audit log entry
        audit_entry = {
            "event": "update_contact_information",
            "patient_id": patient_id,
            "performed_by": performed_by,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
            "old_contact_information": old_contact_info,
            "new_contact_information": new_contact_information,
        }

        # Initialize audit_logs if not present
        if not hasattr(self, "audit_logs"):
            self.audit_logs = {}  # type: ignore

        if patient_id not in self.audit_logs:
            self.audit_logs[patient_id] = []
        self.audit_logs[patient_id].append(audit_entry)

        return {
            "success": True,
            "message": "Contact information updated and change logged."
        }

    def update_provider_information(
        self, 
        provider_id: str, 
        name: str = None, 
        specialization: str = None, 
        contact_information: str = None
    ) -> dict:
        """
        Modify healthcare provider information.

        Args:
            provider_id (str): Unique identifier of the provider to update.
            name (Optional[str]): New name for the provider (if updating).
            specialization (Optional[str]): New specialization for the provider (if updating).
            contact_information (Optional[str]): New contact information for the provider (if updating).

        Returns:
            dict: {
                "success": True,
                "message": "Provider information updated."
            } on success,
            or
            {
                "success": False,
                "error": "reason"
            } on failure.

        Constraints:
            - provider_id must exist.
            - At least one updatable field must be provided.
            - Only 'name', 'specialization', and 'contact_information' may be updated.
        """
        if provider_id not in self.providers:
            return {"success": False, "error": "Provider not found."}

        updatable_fields = {}
        if name is not None:
            updatable_fields["name"] = name
        if specialization is not None:
            updatable_fields["specialization"] = specialization
        if contact_information is not None:
            updatable_fields["contact_information"] = contact_information

        if not updatable_fields:
            return {"success": False, "error": "No update fields provided."}

        for key, value in updatable_fields.items():
            self.providers[provider_id][key] = value

        return {"success": True, "message": "Provider information updated."}

    def log_access_event(
        self,
        user_id: str,
        patient_id: str,
        record_type: str,
        record_id: str,
        action: str,
        timestamp: str,
        description: str = ""
    ) -> dict:
        """
        Add an entry to the audit log for access or change to a patient's record.

        Args:
            user_id (str): ID of the user performing the action (provider or patient).
            patient_id (str): ID of the patient whose record is accessed.
            record_type (str): Type of record ("medical_test_result", "visit_summary", "message").
            record_id (str): Unique identifier of the target record.
            action (str): The action performed (e.g., "viewed", "modified", "deleted").
            timestamp (str): Time of the action (ISO string expected).
            description (str, optional): Additional description or context for the event.

        Returns:
            dict: Success or error dictionary.

        Constraints:
            - Patient must exist.
            - Record must exist and belong to patient for the specified record type.
            - Audit log must be append-only and not throw exceptions.
        """

        # Ensure audit_log exists as a list
        if not hasattr(self, "audit_log"):
            self.audit_log = []

        # Check if patient exists
        if patient_id not in self.patients:
            return { "success": False, "error": f"Patient {patient_id} does not exist." }

        # Validate record_type and find the record dict
        record_maps = {
            "medical_test_result": self.medical_test_results,
            "visit_summary": self.visit_summaries,
            "message": self.messages
        }

        if record_type not in record_maps:
            return { "success": False, "error": "Invalid record_type." }
    
        record_dict = record_maps[record_type]
        if record_id not in record_dict:
            return { "success": False, "error": f"Record {record_id} does not exist." }

        # Check patient association
        record_patient_id = record_dict[record_id].get("patient_id")
        if record_patient_id != patient_id:
            return { "success": False, "error": "Record does not belong to the given patient." }

        # Log entry contents
        entry = {
            "user_id": user_id,
            "patient_id": patient_id,
            "record_type": record_type,
            "record_id": record_id,
            "action": action,
            "timestamp": timestamp,
            "description": description
        }
        self.audit_log.append(entry)
        return {
            "success": True,
            "message": f"Audit log updated for patient {patient_id}."
        }

    def revoke_patient_access(self, patient_id: str) -> dict:
        """
        Temporarily or permanently disable a patient's portal access.

        Args:
            patient_id (str): The identifier of the patient whose access is to be revoked.

        Returns:
            dict: 
                - On success: {"success": True, "message": "Access revoked for patient <patient_id>"}
                - On failure: {"success": False, "error": "Patient not found"}
        Constraints:
            - Only acts if the patient exists.
            - Access can be revoked multiple times (idempotent).
            - Sets 'access_revoked' to True in the patient record.
            - (Optionally) Blanks authentication_credential to prevent login.
        """
        patient = self.patients.get(patient_id)
        if not patient:
            return {"success": False, "error": f"Patient {patient_id} not found"}

        # Mark access as revoked; add attribute if not present
        if "access_revoked" not in patient or patient["access_revoked"] is False:
            patient["access_revoked"] = True
            # Optionally blank authentication credential (stronger block)
            patient["authentication_credential"] = ""
            self.patients[patient_id] = patient
            return {"success": True, "message": f"Access revoked for patient {patient_id}"}
        else:
            # Access already revoked; idempotent operation
            return {"success": True, "message": f"Access is already revoked for patient {patient_id}"}

    def restore_deleted_record(self, user_id: str, record_type: str, record_id: str) -> dict:
        """
        Recover a previously deleted medical record or message if allowed by policy.

        Args:
            user_id (str): ID of the user requesting restoration (patient or provider).
            record_type (str): Type of record to restore ('medical_test_result' or 'message').
            record_id (str): ID of the record to restore.

        Returns:
            dict: {
                "success": True,
                "message": "Record successfully restored."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Only users authorized for the record (record owner patient, relevant provider, or admin)
              can restore.
            - Record must exist in deleted_records buffer for its type.
            - Restoration policy allows the operation (no hard delete, record isn't expired, etc.).
            - Data integrity/auditability should be preserved (could add entry to an audit log).
        """
        # Assume self.deleted_records = {'medical_test_result': {result_id: MedicalTestResultInfo}, 'message': {message_id: MessageInfo}}
        if not hasattr(self, 'deleted_records'):
            return {"success": False, "error": "No deleted record archive found in the system."}

        if record_type not in ("medical_test_result", "message"):
            return {"success": False, "error": "Invalid record type for restoration."}

        deleted_records_of_type = self.deleted_records.get(record_type, {})
        if record_id not in deleted_records_of_type:
            return {"success": False, "error": "No deleted record found with the specified ID."}

        record = copy.deepcopy(deleted_records_of_type[record_id])
        if record.get("__incomplete__"):
            return {"success": False, "error": "Deleted record payload is incomplete in the archive."}

        # Authorization check
        if record_type == "medical_test_result":
            patient_id = record["patient_id"]
            # Only the patient themselves can restore, or (optionally) certain trusted providers (policy detail).
            if user_id != patient_id and user_id not in self.providers:
                return {"success": False, "error": "Permission denied to restore this test result."}
            # Additional policy (e.g., only providers who ordered can restore) can be added here
            # Restore: move back to active records
            record.pop("record_type", None)
            record["result_id"] = record_id
            self.medical_test_results[record_id] = record
        elif record_type == "message":
            patient_id = record["patient_id"]
            # Only patient or sender or receiver in message, or an admin, can restore
            if user_id not in (patient_id, record["sender_id"], record["receiver_id"]) and not self._is_admin_user(user_id):
                return {"success": False, "error": "Permission denied to restore this message."}
            record.pop("record_type", None)
            record["message_id"] = record_id
            self.messages[record_id] = record

        # Remove from deleted records
        del deleted_records_of_type[record_id]

        # Auditability stub (not fully implemented)
        # if hasattr(self, "audit_log"):
        #     self.audit_log.append((user_id, "restore", record_type, record_id))

        return {"success": True, "message": "Record successfully restored."}


class PatientPortalSystem(BaseEnv):
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
        patients = init_config.get("patients", {}) if isinstance(init_config.get("patients"), dict) else {}

        def _normalize_audit_log(value):
            if isinstance(value, list):
                return copy.deepcopy(value)
            if isinstance(value, str):
                text = value.strip()
                if not text:
                    return []
                try:
                    parsed = json.loads(text)
                except Exception:
                    return [value]
                if isinstance(parsed, list):
                    return parsed
                return [parsed]
            return []

        def _normalize_audit_logs(value):
            result = {}
            single_patient_id = next(iter(patients)) if len(patients) == 1 else None

            def _append(patient_id, entry):
                if not patient_id:
                    return
                result.setdefault(patient_id, []).append(entry)

            parsed = value
            if isinstance(value, str):
                text = value.strip()
                if not text:
                    return {}
                try:
                    parsed = json.loads(text)
                except Exception:
                    if single_patient_id is not None:
                        return {single_patient_id: [value]}
                    return {}

            if isinstance(parsed, dict):
                for patient_id, entries in parsed.items():
                    if isinstance(entries, list):
                        result[patient_id] = copy.deepcopy(entries)
                    else:
                        result[patient_id] = [copy.deepcopy(entries)]
                return result

            if isinstance(parsed, list):
                for entry in parsed:
                    if isinstance(entry, dict) and entry.get("patient_id"):
                        _append(entry["patient_id"], copy.deepcopy(entry))
                    elif single_patient_id is not None:
                        _append(single_patient_id, copy.deepcopy(entry))
                return result

            if single_patient_id is not None and parsed:
                return {single_patient_id: [copy.deepcopy(parsed)]}
            return {}

        def _normalize_deleted_records(value):
            archive = {"medical_test_result": {}, "message": {}}
            single_patient_id = next(iter(patients)) if len(patients) == 1 else None

            def _infer_type(record):
                if not isinstance(record, dict):
                    return None
                if record.get("record_type") in {"medical_test_result", "message"}:
                    return record["record_type"]
                if any(k in record for k in ("test_type", "result_units", "ordering_provider", "result_value")):
                    return "medical_test_result"
                if any(k in record for k in ("sender_id", "receiver_id", "content", "message_id")):
                    return "message"
                return None

            def _store(record_type, record_id, record):
                if record_type not in archive or not record_id:
                    return
                normalized = copy.deepcopy(record)
                normalized.setdefault("record_type", record_type)
                if record_type == "medical_test_result":
                    normalized.setdefault("result_id", record_id)
                elif record_type == "message":
                    normalized.setdefault("message_id", record_id)
                archive[record_type][record_id] = normalized

            parsed = value
            if isinstance(value, str):
                text = value.strip()
                if not text:
                    return archive
                try:
                    parsed = json.loads(text)
                except Exception:
                    record_id = text.split(":", 1)[0].strip() if ":" in text else text
                    if record_id:
                        placeholder = {
                            "record_id": record_id,
                            "patient_id": single_patient_id,
                            "__incomplete__": True,
                        }
                        record_type = "message" if record_id.startswith("M-") else "medical_test_result"
                        _store(record_type, record_id, placeholder)
                    return archive

            if isinstance(parsed, dict):
                if set(parsed.keys()).issubset({"medical_test_result", "message"}):
                    for record_type, items in parsed.items():
                        if isinstance(items, dict):
                            for record_id, record in items.items():
                                if isinstance(record, dict):
                                    _store(record_type, record_id, record)
                    return archive
                for record_id, record in parsed.items():
                    if isinstance(record, dict):
                        inferred = _infer_type(record)
                        if inferred:
                            _store(inferred, record_id, record)
                return archive

            if isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, str):
                        placeholder = {
                            "record_id": item,
                            "patient_id": single_patient_id,
                            "__incomplete__": True,
                        }
                        _store("medical_test_result", item, placeholder)
                        continue
                    if isinstance(item, dict):
                        record_type = _infer_type(item)
                        record_id = item.get("record_id") or item.get("result_id") or item.get("message_id")
                        if record_type and record_id:
                            _store(record_type, record_id, item)
                return archive

            return archive

        for key, value in init_config.items():
            if key == "audit_log":
                setattr(env, key, _normalize_audit_log(value))
                continue
            if key == "audit_logs":
                setattr(env, key, _normalize_audit_logs(value))
                continue
            if key == "deleted_records":
                setattr(env, key, _normalize_deleted_records(value))
                continue
            if key == "log_access_event":
                setattr(env, "_log_access_event_state", copy.deepcopy(value))
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

    def get_patient_by_id(self, **kwargs):
        return self._call_inner_tool('get_patient_by_id', kwargs)

    def get_patient_by_auth(self, **kwargs):
        return self._call_inner_tool('get_patient_by_auth', kwargs)

    def list_patient_test_results(self, **kwargs):
        return self._call_inner_tool('list_patient_test_results', kwargs)

    def filter_patient_test_results_by_date(self, **kwargs):
        return self._call_inner_tool('filter_patient_test_results_by_date', kwargs)

    def filter_patient_test_results_by_type(self, **kwargs):
        return self._call_inner_tool('filter_patient_test_results_by_type', kwargs)

    def get_test_result_by_id(self, **kwargs):
        return self._call_inner_tool('get_test_result_by_id', kwargs)

    def list_patient_visit_summaries(self, **kwargs):
        return self._call_inner_tool('list_patient_visit_summaries', kwargs)

    def filter_patient_visit_summaries_by_date(self, **kwargs):
        return self._call_inner_tool('filter_patient_visit_summaries_by_date', kwargs)

    def get_provider_by_id(self, **kwargs):
        return self._call_inner_tool('get_provider_by_id', kwargs)

    def list_providers(self, **kwargs):
        return self._call_inner_tool('list_providers', kwargs)

    def list_patient_messages(self, **kwargs):
        return self._call_inner_tool('list_patient_messages', kwargs)

    def filter_patient_messages_by_date(self, **kwargs):
        return self._call_inner_tool('filter_patient_messages_by_date', kwargs)

    def get_message_by_id(self, **kwargs):
        return self._call_inner_tool('get_message_by_id', kwargs)

    def check_record_access_rights(self, **kwargs):
        return self._call_inner_tool('check_record_access_rights', kwargs)

    def get_audit_log_for_patient(self, **kwargs):
        return self._call_inner_tool('get_audit_log_for_patient', kwargs)

    def add_medical_test_result(self, **kwargs):
        return self._call_inner_tool('add_medical_test_result', kwargs)

    def update_medical_test_result(self, **kwargs):
        return self._call_inner_tool('update_medical_test_result', kwargs)

    def delete_medical_test_result(self, **kwargs):
        return self._call_inner_tool('delete_medical_test_result', kwargs)

    def add_visit_summary(self, **kwargs):
        return self._call_inner_tool('add_visit_summary', kwargs)

    def update_visit_summary(self, **kwargs):
        return self._call_inner_tool('update_visit_summary', kwargs)

    def add_message(self, **kwargs):
        return self._call_inner_tool('add_message', kwargs)

    def update_patient_contact_information(self, **kwargs):
        return self._call_inner_tool('update_patient_contact_information', kwargs)

    def update_provider_information(self, **kwargs):
        return self._call_inner_tool('update_provider_information', kwargs)

    def log_access_event(self, **kwargs):
        return self._call_inner_tool('log_access_event', kwargs)

    def revoke_patient_access(self, **kwargs):
        return self._call_inner_tool('revoke_patient_access', kwargs)

    def restore_deleted_record(self, **kwargs):
        return self._call_inner_tool('restore_deleted_record', kwargs)
