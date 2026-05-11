# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



class StudyInfo(TypedDict):
    study_id: str
    title: str
    protocol_id: str
    description: str
    status: str
    eligibility_criteria: str
    start_date: str
    end_date: str
    site_ids: List[str]
    investigator_id: str

class ProtocolInfo(TypedDict):
    protocol_id: str
    study_id: str
    procedures: str
    schedule: str
    regulatory_status: str

class InvestigatorInfo(TypedDict):
    investigator_id: str
    name: str
    contact_info: str
    affiliation: str

class SiteInfo(TypedDict):
    site_id: str
    name: str
    address: str
    contact_info: str

class ParticipantInfo(TypedDict):
    participant_id: str
    name: str
    contact_info: str
    enrollment_status: str
    eligible_study_id: str

class CommunicationInfo(TypedDict):
    communication_id: str
    participant_id: str
    study_id: str
    timestamp: str
    subject: str
    message_content: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Studies: {study_id: StudyInfo}
        self.studies: Dict[str, StudyInfo] = {}
        # Protocols: {protocol_id: ProtocolInfo}
        self.protocols: Dict[str, ProtocolInfo] = {}
        # Investigators: {investigator_id: InvestigatorInfo}
        self.investigators: Dict[str, InvestigatorInfo] = {}
        # Sites: {site_id: SiteInfo}
        self.sites: Dict[str, SiteInfo] = {}
        # Participants: {participant_id: ParticipantInfo}
        self.participants: Dict[str, ParticipantInfo] = {}
        # Communications: {communication_id: CommunicationInfo}
        self.communications: Dict[str, CommunicationInfo] = {}

        # Constraints/rules:
        # - Studies must have valid protocols and at least one investigator.
        # - Study information query by ID must return only studies that are active or currently recruiting.
        # - Enrolling participants must pass eligibility checks based on study criteria.
        # - Regulatory status must be tracked for all active studies.
        # - Sites and investigators must be linked to valid, ongoing studies.

    def get_study_by_id(self, study_id: str) -> dict:
        """
        Retrieve information about a study by study_id, but only if the study is 'active' or 'recruiting'.

        Args:
            study_id (str): The unique identifier for the study.

        Returns:
            dict: 
                - On success: {"success": True, "data": StudyInfo}
                - On failure (not found or not active/recruiting): {"success": False, "error": str}

        Constraints:
            - The study must exist.
            - The study status must be 'active' or 'recruiting'.
        """
        study = self.studies.get(study_id)
        if study is None:
            return {"success": False, "error": "Study not found."}
        if study.get("status") not in {"active", "recruiting"}:
            return {"success": False, "error": "Study is not active or recruiting."}
        return {"success": True, "data": study}

    def list_all_studies(self, status: str = None) -> dict:
        """
        Return a list of all studies, with optional filtering by status.

        Args:
            status (str, optional): If provided, only studies with this status (e.g., "active", "recruiting", "completed")
                                   will be returned. Otherwise, all studies are included.

        Returns:
            dict: {
                "success": True,
                "data": List[StudyInfo],   # All matching studies
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - No filtering by default, unless status is provided.
            - If status is given but invalid (not str or None), operation fails.
        """
        if status is not None and not isinstance(status, str):
            return { "success": False, "error": "Status filter must be a string or None." }

        if status is None:
            result = list(self.studies.values())
        else:
            result = [study for study in self.studies.values() if study.get("status") == status]

        return { "success": True, "data": result }

    def get_protocol_by_study_id(self, study_id: str) -> dict:
        """
        Fetch the protocol details associated with a given study_id.

        Args:
            study_id (str): The identifier of the study.

        Returns:
            dict:
                - success: True and data (ProtocolInfo) if a protocol for the study exists.
                - success: False and error (str) if not found.

        Constraints:
            - The study must exist.
            - There must be a protocol record with ProtocolInfo.study_id matching the input study_id.
        """
        if not study_id or study_id not in self.studies:
            return { "success": False, "error": "Study does not exist" }
    
        # Look for the protocol associated with this study
        for protocol in self.protocols.values():
            if protocol["study_id"] == study_id:
                return { "success": True, "data": protocol }
    
        return { "success": False, "error": "No protocol found for the given study_id" }

    def get_investigator_by_study_id(self, study_id: str) -> dict:
        """
        Retrieve information about the investigator linked to a specified study.

        Args:
            study_id (str): The unique identifier of the study.

        Returns:
            dict:
                {
                    "success": True,
                    "data": InvestigatorInfo  # investigator's info if found and allowed
                }
                OR
                {
                    "success": False,
                    "error": str  # Reason for failure
                }

        Constraints:
            - Study must exist and be in 'active' or 'recruiting' status.
            - Study must have a valid investigator_id.
        """
        study = self.studies.get(study_id)
        if not study:
            return {"success": False, "error": "Study not found"}

        if study["status"].lower() not in ["active", "recruiting"]:
            return {"success": False, "error": "Study is not active or recruiting"}

        investigator_id = study.get("investigator_id")
        if not investigator_id:
            return {"success": False, "error": "No investigator linked to this study"}

        investigator = self.investigators.get(investigator_id)
        if not investigator:
            return {"success": False, "error": "Investigator not found"}

        return {"success": True, "data": investigator}

    def get_sites_by_study_id(self, study_id: str) -> dict:
        """
        Obtain details for all sites involved in a particular study.

        Args:
            study_id (str): The unique identifier of the study.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[SiteInfo]  # Empty if no sites or study found
                }
                or
                {
                    "success": False,
                    "error": str  # "Study not found"
                }

        Constraints:
            - The study must exist in the system.
            - Only return existing sites listed in the study's site_ids.
        """
        study = self.studies.get(study_id)
        if not study:
            return { "success": False, "error": "Study not found" }

        site_ids = study.get("site_ids", [])
        site_infos = [
            self.sites[site_id]
            for site_id in site_ids
            if site_id in self.sites
        ]

        return { "success": True, "data": site_infos }

    def get_regulatory_status_by_study_id(self, study_id: str) -> dict:
        """
        Retrieve the regulatory status of the study's protocol given a study_id.

        Args:
            study_id (str): The unique identifier for the study.

        Returns:
            dict: {
                "success": True,
                "data": str    # regulatory_status
            }
            or
            {
                "success": False,
                "error": str   # Error description
            }

        Constraints:
            - Only studies with status "active" or "currently recruiting" are eligible.
            - The study must exist and have a valid protocol.
        """
        study = self.studies.get(study_id)
        if not study or study["status"].lower() not in {"active", "currently recruiting"}:
            return {
                "success": False,
                "error": "Study not found or unavailable for regulatory status query"
            }
        protocol_id = study.get("protocol_id")
        protocol = self.protocols.get(protocol_id)
        if not protocol:
            return {
                "success": False,
                "error": "Protocol not found for the specified study"
            }
        # protocol is found, return its regulatory status
        return {
            "success": True,
            "data": protocol["regulatory_status"]
        }

    def get_participants_by_study_id(self, study_id: str) -> dict:
        """
        List all participants registered or eligible for a given study.

        Args:
            study_id (str): The ID of the study for which participants are requested.

        Returns:
            dict: {
                "success": True,
                "data": List[ParticipantInfo]  # List of matching participant info dicts
            }
            OR
            {
                "success": False,
                "error": str  # If study not found
            }

        Constraints:
            - The study with study_id must exist.
            - Both registered and merely eligible participants (those where eligible_study_id == study_id) are returned.
        """
        if study_id not in self.studies:
            return { "success": False, "error": "Study not found" }
    
        participants = [
            pinfo for pinfo in self.participants.values()
            if pinfo.get("eligible_study_id") == study_id
        ]
        return { "success": True, "data": participants }

    def get_participant_by_id(self, participant_id: str) -> dict:
        """
        Retrieve details for a specific participant by their participant_id.

        Args:
            participant_id (str): The unique identifier for the participant.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": ParticipantInfo  # The participant's information
                    }
                On failure (participant not found):
                    {
                        "success": False,
                        "error": "Participant not found"
                    }
        Constraints:
            - The participant_id must exist in the system.
        """
        participant = self.participants.get(participant_id)
        if participant is None:
            return { "success": False, "error": "Participant not found" }
        return { "success": True, "data": participant }

    def get_communications_by_study_id(self, study_id: str) -> dict:
        """
        Fetch all communications related to a specific study.

        Args:
            study_id (str): The ID of the target study.
    
        Returns:
            dict: 
              Success: {
                  "success": True,
                  "data": List[CommunicationInfo],   # All communications linked to given study_id (may be empty)
              }
              Error: {
                  "success": False,
                  "error": str,     # Study not found
              }

        Constraints:
            - study_id must exist in the system (in self.studies).
            - No restriction on study status for this operation.
        """
        if study_id not in self.studies:
            return {"success": False, "error": "Study not found"}

        communications = [
            comm for comm in self.communications.values()
            if comm["study_id"] == study_id
        ]
        return {"success": True, "data": communications}

    def get_communications_by_participant_id(self, participant_id: str) -> dict:
        """
        Fetch all communications related to a specific participant.

        Args:
            participant_id (str): The unique ID of the participant.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[CommunicationInfo],  # list of communications for the participant (empty if none)
                }
                or
                {
                    "success": False,
                    "error": str  # If participant does not exist
                }

        Constraints:
            - participant_id must exist in the system.
        """
        if participant_id not in self.participants:
            return {"success": False, "error": "Participant does not exist"}
    
        participant_communications = [
            comm for comm in self.communications.values()
            if comm["participant_id"] == participant_id
        ]
        return {"success": True, "data": participant_communications}

    def check_participant_eligibility(self, participant_id: str, study_id: str) -> dict:
        """
        Evaluate if a participant meets the eligibility criteria for a specific study.

        Args:
            participant_id (str): The ID of the participant to check.
            study_id (str): The ID of the study to check against.

        Returns:
            dict:
                On success:
                {
                    "success": True,
                    "eligible": bool,
                    "details": str  # explanation
                }
                On failure:
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - The study must exist and be active or recruiting.
            - The participant must exist.
            - Simple eligibility check: if participant.eligible_study_id == study_id, treated as eligible.
              (In a real implementation, compare relevant participant info to study.eligibility_criteria)
        """
        study = self.studies.get(study_id)
        if study is None:
            return {"success": False, "error": "Study does not exist"}

        if study['status'].lower() not in ['active', 'recruiting']:
            return {"success": False, "error": "Study is not currently active or recruiting"}

        participant = self.participants.get(participant_id)
        if participant is None:
            return {"success": False, "error": "Participant does not exist"}

        # Basic eligibility logic for demo: eligible if eligible_study_id matches AND not withdrawn
        eligible = False
        explanation = ""
        if participant.get("eligible_study_id") == study_id:
            if participant.get("enrollment_status", "").lower() not in ['withdrawn', 'ineligible']:
                eligible = True
                explanation = "Participant is eligible: eligible_study_id matches and enrollment_status is not withdrawn/ineligible."
            else:
                eligible = False
                explanation = f"Participant enrollment_status is '{participant.get('enrollment_status')}', not eligible."
        else:
            eligible = False
            explanation = "Participant's eligible_study_id does not match this study."

        return {
            "success": True,
            "eligible": eligible,
            "details": explanation
        }

    def add_study(
        self,
        study_id: str,
        title: str,
        protocol_id: str,
        description: str,
        status: str,
        eligibility_criteria: str,
        start_date: str,
        end_date: str,
        site_ids: list,
        investigator_id: str,
    ) -> dict:
        """
        Register a new study, ensuring protocol and investigator linkage.

        Args:
            study_id (str): Unique identifier for the study.
            title (str): Study title.
            protocol_id (str): Must correspond to an existing protocol.
            description (str): Description of the study.
            status (str): Study status (e.g., Active, Recruiting, etc.).
            eligibility_criteria (str): Eligibility requirements for participants.
            start_date (str): Study start date (format assumed consistent).
            end_date (str): Study end date.
            site_ids (List[str]): List of site IDs where the study is conducted.
            investigator_id (str): Must correspond to an existing investigator.

        Returns:
            dict: {
                "success": True,
                "message": "Study registered successfully"
            }
            or
            {
                "success": False,
                "error": "Reason for failure"
            }

        Constraints:
            - study_id must be unique.
            - protocol_id must exist.
            - investigator_id must exist.
            - Each site_id must exist if site_ids is provided.
            - Protocol's study_id is linked to this study.
        """
        # Uniqueness constraint
        if study_id in self.studies:
            return { "success": False, "error": "Study ID already exists." }
    
        # Protocol linkage constraint
        if protocol_id not in self.protocols:
            return { "success": False, "error": "Protocol ID does not exist." }
    
        # Investigator linkage constraint
        if investigator_id not in self.investigators:
            return { "success": False, "error": "Investigator ID does not exist." }
    
        # Site IDs validation
        invalid_sites = [sid for sid in site_ids if sid not in self.sites]
        if invalid_sites:
            return {
                "success": False,
                "error": f"Invalid site IDs: {', '.join(invalid_sites)}"
            }
    
        # Register study
        study_entry = {
            "study_id": study_id,
            "title": title,
            "protocol_id": protocol_id,
            "description": description,
            "status": status,
            "eligibility_criteria": eligibility_criteria,
            "start_date": start_date,
            "end_date": end_date,
            "site_ids": site_ids,
            "investigator_id": investigator_id,
        }
        self.studies[study_id] = study_entry

        # Update protocol info to set correct study_id
        self.protocols[protocol_id]["study_id"] = study_id

        return {
            "success": True,
            "message": "Study registered successfully"
        }

    def update_study_info(self, study_id: str, updates: dict) -> dict:
        """
        Modify fields of an existing study record.

        Args:
            study_id (str): ID of the study to update.
            updates (dict): Key-value pairs of fields to update. Allowed fields are:
                - title
                - description
                - status
                - eligibility_criteria
                - start_date
                - end_date
                - protocol_id (must exist in protocols)
                - investigator_id (must exist in investigators)
                - site_ids (must be list of valid site_ids)

        Returns:
            dict: {
                "success": True,
                "message": "Study information updated."
            }
            or
            {
                "success": False,
                "error": "description"
            }

        Constraints:
            - Study must exist.
            - protocol_id, investigator_id, and site_ids (if changed) must be valid.
            - After update, study must still have valid protocol and at least one investigator.
            - Non-updateable fields (like study_id) will be ignored.
        """
        # Check existence
        if study_id not in self.studies:
            return { "success": False, "error": "Study does not exist." }

        allowed_fields = {
            "title", "description", "status",
            "eligibility_criteria", "start_date", "end_date",
            "protocol_id", "investigator_id", "site_ids"
        }
        study = self.studies[study_id]
        original_protocol_id = study.get("protocol_id")

        for key, value in updates.items():
            if key not in allowed_fields:
                return { "success": False, "error": f"Field '{key}' is not allowed to be updated." }

            # Validate protocol_id if being updated
            if key == "protocol_id":
                if value not in self.protocols:
                    return { "success": False, "error": f"Protocol ID '{value}' does not exist." }
                study["protocol_id"] = value

            # Validate investigator_id if being updated
            elif key == "investigator_id":
                if value not in self.investigators:
                    return { "success": False, "error": f"Investigator ID '{value}' does not exist." }
                study["investigator_id"] = value

            # Validate site_ids if being updated
            elif key == "site_ids":
                if not isinstance(value, list):
                    return { "success": False, "error": f"'site_ids' must be a list." }
                for site_id in value:
                    if site_id not in self.sites:
                        return { "success": False, "error": f"Site ID '{site_id}' does not exist." }
                study["site_ids"] = value

            # Basic field update
            else:
                study[key] = value

        # Constraint: Study must have a valid protocol and at least one investigator
        updated_protocol_id = study.get("protocol_id")
        updated_investigator_id = study.get("investigator_id")
        if (not updated_protocol_id) or (updated_protocol_id not in self.protocols):
            return {"success": False, "error": "Study must be linked to a valid protocol."}
        if (not updated_investigator_id) or (updated_investigator_id not in self.investigators):
            return {"success": False, "error": "Study must have at least one valid investigator."}

        if original_protocol_id != updated_protocol_id:
            old_protocol = self.protocols.get(original_protocol_id)
            if old_protocol and old_protocol.get("study_id") == study_id:
                old_protocol["study_id"] = ""
            self.protocols[updated_protocol_id]["study_id"] = study_id

        self.studies[study_id] = study
        return { "success": True, "message": "Study information updated." }

    def update_study_status(self, study_id: str, new_status: str) -> dict:
        """
        Update the status of a clinical study.

        Args:
            study_id (str): Unique identifier of the study to update.
            new_status (str): The new status to set. Must be one of the accepted statuses:
                              ("planned", "recruiting", "active", "completed", "terminated")

        Returns:
            dict: {
                "success": True,
                "message": "Study status updated successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - study_id must exist in the system.
            - new_status must be a valid status string.
        """
        VALID_STATUSES = {"planned", "recruiting", "active", "completed", "terminated"}

        # Check study existence
        if study_id not in self.studies:
            return { "success": False, "error": "Study not found." }

        # Validate new status
        if new_status not in VALID_STATUSES:
            return { "success": False, "error": f"Invalid status: '{new_status}'. Allowed: {', '.join(VALID_STATUSES)}" }

        # Update status
        self.studies[study_id]["status"] = new_status

        # (Optionally update other timestamp/fields here if needed for a real system)

        return { "success": True, "message": "Study status updated successfully." }

    def add_protocol(
        self,
        protocol_id: str,
        study_id: str,
        procedures: str,
        schedule: str,
        regulatory_status: str
    ) -> dict:
        """
        Add a new protocol and associate it with a specified study.

        Args:
            protocol_id (str): Unique identifier for the protocol
            study_id (str): Identifier of the study to link the protocol to
            procedures (str): Description of study procedures
            schedule (str): Study schedule information
            regulatory_status (str): Regulatory status of the protocol

        Returns:
            dict: {
                "success": True, "message": str
            } on success,
            {
                "success": False, "error": str
            } on error

        Constraints:
            - protocol_id must not already exist.
            - study_id must exist.
            - Regulatory status must be tracked (required field).
        """
        # Check uniqueness of protocol_id
        if protocol_id in self.protocols:
            return {
                "success": False,
                "error": f"Protocol with id '{protocol_id}' already exists."
            }

        # Check existence of study_id
        if study_id not in self.studies:
            return {
                "success": False,
                "error": f"Study with id '{study_id}' does not exist."
            }

        # Add the protocol
        protocol: ProtocolInfo = {
            "protocol_id": protocol_id,
            "study_id": study_id,
            "procedures": procedures,
            "schedule": schedule,
            "regulatory_status": regulatory_status
        }
        self.protocols[protocol_id] = protocol
        self.studies[study_id]["protocol_id"] = protocol_id

        return {
            "success": True,
            "message": f"Protocol '{protocol_id}' added and linked to study '{study_id}'."
        }

    def update_protocol(
        self,
        protocol_id: str,
        procedures: str = None,
        schedule: str = None,
        regulatory_status: str = None
    ) -> dict:
        """
        Modify details or regulatory status of an existing protocol.

        Args:
            protocol_id (str): The protocol to update.
            procedures (str, optional): New procedures outline.
            schedule (str, optional): New schedule.
            regulatory_status (str, optional): Updated regulatory status.

        Returns:
            dict:
                - success: True, with confirmation message if protocol is updated.
                - success: False, with error message if protocol ID not found or no update fields are provided.

        Constraints:
            - The protocol to be updated must exist.
            - At least one field to update must be provided.
            - Updates apply only to specified fields.
        """
        if protocol_id not in self.protocols:
            return {"success": False, "error": "Protocol ID not found."}

        if procedures is None and schedule is None and regulatory_status is None:
            return {"success": False, "error": "No update fields specified."}

        protocol = self.protocols[protocol_id]

        if procedures is not None:
            protocol["procedures"] = procedures
        if schedule is not None:
            protocol["schedule"] = schedule
        if regulatory_status is not None:
            protocol["regulatory_status"] = regulatory_status

        self.protocols[protocol_id] = protocol  # Save changes

        return {"success": True, "message": "Protocol updated successfully."}

    def assign_investigator_to_study(self, study_id: str, investigator_id: str) -> dict:
        """
        Assign (link) an investigator to a given study.

        Args:
            study_id (str): The ID of the study to be updated.
            investigator_id (str): The investigator to be linked to the study.

        Returns:
            dict: {
                "success": True,
                "message": "Investigator <investigator_id> assigned to study <study_id>."
            }
            or
            {
                "success": False,
                "error": <str>
            }

        Constraints:
            - The study must exist.
            - The investigator must exist.
            - A study must always have at least one investigator.
        """
        if study_id not in self.studies:
            return { "success": False, "error": f"Study with ID '{study_id}' does not exist." }
        if investigator_id not in self.investigators:
            return { "success": False, "error": f"Investigator with ID '{investigator_id}' does not exist." }

        self.studies[study_id]["investigator_id"] = investigator_id

        return {
            "success": True,
            "message": f"Investigator '{investigator_id}' assigned to study '{study_id}'."
        }

    def add_site_to_study(self, study_id: str, site_id: str) -> dict:
        """
        Attach a site (site_id) to a specified study (study_id).
    
        Args:
            study_id (str): Identifier for the clinical study.
            site_id (str): Identifier for the site (hospital or research location).
        
        Returns:
            dict: Success or failure with appropriate message.
            On success:
                {
                    "success": True,
                    "message": "Site '<site_id>' added to study '<study_id>'."
                }
            On failure:
                {
                    "success": False,
                    "error": "<reason>"
                }
        
        Constraints:
            - Both study and site must exist.
            - Sites cannot be added multiple times to the same study.
            - Study must be 'active' or 'recruiting' to allow modifications.
        """
        study = self.studies.get(study_id)
        if not study:
            return {"success": False, "error": f"Study '{study_id}' does not exist."}
        site = self.sites.get(site_id)
        if not site:
            return {"success": False, "error": f"Site '{site_id}' does not exist."}
        if study["status"].lower() not in ("active", "recruiting", "currently recruiting"):
            return {
                "success": False,
                "error": f"Cannot modify study '{study_id}' because its status is not active or recruiting."
            }
        if site_id in study["site_ids"]:
            return {"success": False, "error": f"Site '{site_id}' is already attached to study '{study_id}'."}
        study["site_ids"].append(site_id)
        self.studies[study_id] = study  # For explicit state update, if needed.
        return {"success": True, "message": f"Site '{site_id}' added to study '{study_id}'."}

    def enroll_participant_in_study(self, participant_id: str, study_id: str) -> dict:
        """
        Enroll a participant in a study after eligibility is checked.

        Args:
            participant_id (str): ID of the participant to enroll.
            study_id (str): ID of the study to enroll into.

        Returns:
            dict: {
                "success": True,
                "message": "Participant enrolled in study."
            }
            or
            {
                "success": False,
                "error": <str(reason)>
            }

        Constraints:
            - Study must exist and be active or recruiting.
            - Participant must exist.
            - Participant must pass eligibility check based on study criteria.
            - If already enrolled in this study, returns an appropriate message.
        """

        # Check participant existence
        participant = self.participants.get(participant_id)
        if not participant:
            return { "success": False, "error": "Participant does not exist" }

        # Check study existence
        study = self.studies.get(study_id)
        if not study:
            return { "success": False, "error": "Study does not exist" }

        # Check study status (must be 'active' or 'recruiting')
        valid_statuses = ['active', 'recruiting']
        if study['status'].lower() not in valid_statuses:
            return { "success": False, "error": f"Study is not enrolling participants (status: {study['status']})" }

        # Check if participant already enrolled
        if (participant.get("enrollment_status") == "enrolled" and
            participant.get("eligible_study_id") == study_id):
            return { "success": False, "error": "Participant is already enrolled in this study" }

        # Simulate eligibility check (here: simple string containment, as eligibility_criteria logic is not defined)
        # Example: check if participant's eligible_study_id matches or set to blank
        # (You could replace or improve this section with detailed logic)
        if participant.get("eligible_study_id") not in (study_id, "", None):
            return { "success": False, "error": "Participant is not eligible for this study" }

        # Enrollment: update participant info
        participant["enrollment_status"] = "enrolled"
        participant["eligible_study_id"] = study_id
        self.participants[participant_id] = participant

        return { "success": True, "message": "Participant enrolled in study." }

    def update_participant_status(self, participant_id: str, new_status: str) -> dict:
        """
        Change the enrollment status of a participant.

        Args:
            participant_id (str): Identifier of the participant whose status is to be updated.
            new_status (str): The new enrollment status (e.g., "screening", "enrolled", "withdrawn").

        Returns:
            dict: {
                "success": True,
                "message": "Participant status updated to <new_status>"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Participant must exist.
            - No restrictions on allowed status strings unless validated elsewhere.
        """
        participant = self.participants.get(participant_id)
        if not participant:
            return {"success": False, "error": "Participant does not exist"}

        participant["enrollment_status"] = new_status
        return {"success": True, "message": f"Participant status updated to {new_status}"}

    def add_communication(
        self,
        communication_id: str,
        participant_id: str,
        study_id: str,
        timestamp: str,
        subject: str,
        message_content: str
    ) -> dict:
        """
        Record a new communication between a participant and study staff.

        Args:
            communication_id (str): Unique identifier for the communication.
            participant_id (str): ID of the participant involved.
            study_id (str): ID of the study related to the communication.
            timestamp (str): Timestamp of the communication (e.g. ISO8601 string).
            subject (str): Subject/title of the message.
            message_content (str): Body/content of the message.

        Returns:
            dict: {
                "success": True,
                "message": "Communication recorded successfully."
            } on success,
            or
            {
                "success": False,
                "error": "reason for failure"
            }

        Constraints:
            - communication_id must be unique.
            - participant_id must exist.
            - study_id must exist.
        """

        if communication_id in self.communications:
            return { "success": False, "error": "Communication ID already exists." }

        if participant_id not in self.participants:
            return { "success": False, "error": "Participant ID does not exist." }

        if study_id not in self.studies:
            return { "success": False, "error": "Study ID does not exist." }

        # Optionally: subject/message_content not empty checks
        # (omitted unless strictly required)

        comm_entry = {
            "communication_id": communication_id,
            "participant_id": participant_id,
            "study_id": study_id,
            "timestamp": timestamp,
            "subject": subject,
            "message_content": message_content
        }
        self.communications[communication_id] = comm_entry

        return { "success": True, "message": "Communication recorded successfully." }

    def remove_participant_from_study(self, participant_id: str, study_id: str) -> dict:
        """
        Remove (withdraw) a participant from a study and update their status.

        Args:
            participant_id (str): Unique identifier of the participant.
            study_id (str): Unique identifier of the study.

        Returns:
            dict:
                {
                    "success": True,
                    "message": "Participant <id> removed from study <id>."
                }
                or
                {
                    "success": False,
                    "error": <reason>
                }

        Constraints:
            - Participant and study must exist.
            - Participant must currently be associated with (enrolled in) the specified study.
            - Participant's enrollment_status is updated to 'withdrawn', and eligible_study_id cleared.
        """
        # Check participant existence
        if participant_id not in self.participants:
            return {"success": False, "error": f"Participant '{participant_id}' does not exist."}
        # Check study existence
        if study_id not in self.studies:
            return {"success": False, "error": f"Study '{study_id}' does not exist."}

        participant = self.participants[participant_id]
        # Check that this participant is enrolled in the given study
        if participant["eligible_study_id"] != study_id or participant["enrollment_status"] not in ("enrolled", "active"):
            return {
                "success": False,
                "error": f"Participant '{participant_id}' is not enrolled in study '{study_id}'."
            }

        # Update participant status
        participant["enrollment_status"] = "withdrawn"
        participant["eligible_study_id"] = ""

        self.participants[participant_id] = participant

        return {
            "success": True,
            "message": f"Participant '{participant_id}' removed from study '{study_id}'."
        }


class ClinicalTrialManagementSystem(BaseEnv):
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

    def get_study_by_id(self, **kwargs):
        return self._call_inner_tool('get_study_by_id', kwargs)

    def list_all_studies(self, **kwargs):
        return self._call_inner_tool('list_all_studies', kwargs)

    def get_protocol_by_study_id(self, **kwargs):
        return self._call_inner_tool('get_protocol_by_study_id', kwargs)

    def get_investigator_by_study_id(self, **kwargs):
        return self._call_inner_tool('get_investigator_by_study_id', kwargs)

    def get_sites_by_study_id(self, **kwargs):
        return self._call_inner_tool('get_sites_by_study_id', kwargs)

    def get_regulatory_status_by_study_id(self, **kwargs):
        return self._call_inner_tool('get_regulatory_status_by_study_id', kwargs)

    def get_participants_by_study_id(self, **kwargs):
        return self._call_inner_tool('get_participants_by_study_id', kwargs)

    def get_participant_by_id(self, **kwargs):
        return self._call_inner_tool('get_participant_by_id', kwargs)

    def get_communications_by_study_id(self, **kwargs):
        return self._call_inner_tool('get_communications_by_study_id', kwargs)

    def get_communications_by_participant_id(self, **kwargs):
        return self._call_inner_tool('get_communications_by_participant_id', kwargs)

    def check_participant_eligibility(self, **kwargs):
        return self._call_inner_tool('check_participant_eligibility', kwargs)

    def add_study(self, **kwargs):
        return self._call_inner_tool('add_study', kwargs)

    def update_study_info(self, **kwargs):
        return self._call_inner_tool('update_study_info', kwargs)

    def update_study_status(self, **kwargs):
        return self._call_inner_tool('update_study_status', kwargs)

    def add_protocol(self, **kwargs):
        return self._call_inner_tool('add_protocol', kwargs)

    def update_protocol(self, **kwargs):
        return self._call_inner_tool('update_protocol', kwargs)

    def assign_investigator_to_study(self, **kwargs):
        return self._call_inner_tool('assign_investigator_to_study', kwargs)

    def add_site_to_study(self, **kwargs):
        return self._call_inner_tool('add_site_to_study', kwargs)

    def enroll_participant_in_study(self, **kwargs):
        return self._call_inner_tool('enroll_participant_in_study', kwargs)

    def update_participant_status(self, **kwargs):
        return self._call_inner_tool('update_participant_status', kwargs)

    def add_communication(self, **kwargs):
        return self._call_inner_tool('add_communication', kwargs)

    def remove_participant_from_study(self, **kwargs):
        return self._call_inner_tool('remove_participant_from_study', kwargs)
