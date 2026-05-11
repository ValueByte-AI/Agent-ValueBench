# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



class PartyInfo(TypedDict):
    party_id: str
    name: str
    role: str
    contact_information: str

class LegalEventInfo(TypedDict):
    event_id: str
    case_number: str
    date: str
    event_type: str
    description: str

class DocumentInfo(TypedDict):
    document_id: str
    case_number: str
    file_name: str
    file_type: str
    upload_date: str
    access_level: str

class UserInfo(TypedDict):
    _id: str
    name: str
    role: str
    permission: str

class CaseInfo(TypedDict):
    case_number: str
    case_type: str
    filing_date: str
    status: str
    involved_parties: List[str]      # List of party_id
    legal_events: List[str]          # List of event_id
    documents: List[str]             # List of document_id
    assigned_judge: str
    court_location: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Court Case Management System stateful environment.

        Constraints:
        - Each case_number must be unique.
        - Parties must have assigned roles within each case (e.g., plaintiff, defendant, attorney).
        - Only authorized users with proper permissions can view or update certain case details or documents.
        - Status of a case is determined by the latest legal event or manual update by an authorized user.
        - Documents must be associated with valid cases.
        """

        # Cases: {case_number: CaseInfo}
        self.cases: Dict[str, CaseInfo] = {}

        # Parties: {party_id: PartyInfo}
        self.parties: Dict[str, PartyInfo] = {}

        # Legal Events: {event_id: LegalEventInfo}
        self.legal_events: Dict[str, LegalEventInfo] = {}

        # Documents: {document_id: DocumentInfo}
        self.documents: Dict[str, DocumentInfo] = {}

        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Per-case party roles: {(case_number, party_id): role}
        self._case_party_roles: Dict[tuple, str] = {}

        # Optional per-user limit for successful document metadata updates.
        self.document_update_limits: Dict[str, int] = {}
        self.document_update_usage: Dict[str, int] = {}

    def _get_party_role_for_case(self, case_number: str, party_id: str) -> str:
        if (case_number, party_id) in self._case_party_roles:
            return self._case_party_roles[(case_number, party_id)]
        party = self.parties.get(party_id, {})
        return party.get("role", "")

    @staticmethod
    def _is_case_admin_user(user: dict) -> bool:
        if not user:
            return False
        if user.get("role") == "admin":
            return True
        if user.get("permission") in {"admin", "high"}:
            return True
        return False


    def get_case_by_number(self, case_number: str) -> dict:
        """
        Retrieve all details for a given case number, including:
        - Basic case metadata
        - Status
        - Involved parties (expanded)
        - Legal events (expanded)
        - Documents (expanded)
        - Assigned judge
        - Court location

        Args:
            case_number (str): Unique case identifier.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "case_number": ...,
                    "case_type": ...,
                    "filing_date": ...,
                    "status": ...,
                    "involved_parties": List[PartyInfo],
                    "legal_events": List[LegalEventInfo],
                    "documents": List[DocumentInfo],
                    "assigned_judge": ...,
                    "court_location": ...
                }
            }
            OR
            {
                "success": False,
                "error": "Case not found"
            }
        Constraints:
            - Only the case_number must be valid.
            - If referenced party/event/document IDs are missing from dictionaries, they are omitted.
        """
        case = self.cases.get(case_number)
        if not case:
            return {"success": False, "error": "Case not found"}

        # Expand parties
        parties = [
            {
                **self.parties[party_id],
                "role": self._get_party_role_for_case(case_number, party_id),
            }
            for party_id in case["involved_parties"]
            if party_id in self.parties
        ]
        # Expand events
        events = [
            self.legal_events[event_id]
            for event_id in case["legal_events"]
            if event_id in self.legal_events
        ]
        # Expand documents
        documents = [
            self.documents[doc_id]
            for doc_id in case["documents"]
            if doc_id in self.documents
        ]

        result = {
            "case_number": case["case_number"],
            "case_type": case["case_type"],
            "filing_date": case["filing_date"],
            "status": case["status"],
            "involved_parties": parties,
            "legal_events": events,
            "documents": documents,
            "assigned_judge": case["assigned_judge"],
            "court_location": case["court_location"]
        }
        if "closure_request_note" in case:
            result["closure_request_note"] = case["closure_request_note"]
        return {"success": True, "data": result}

    def get_case_status(self, case_number: str) -> dict:
        """
        Retrieve the current status for a given case_number.
    
        Args:
            case_number (str): Unique identifier for the case.
    
        Returns:
            dict:
                success: True and data: status string if found.
                success: False and error: description if case not found.
    
        Constraints:
            - The case_number must exist in the system.
        """
        case = self.cases.get(case_number)
        if not case:
            return {"success": False, "error": "Case not found"}

        status = case.get("status", "")
        return {"success": True, "data": status}

    def list_cases_by_party(self, party_id: str) -> dict:
        """
        Retrieve all cases in which the specified party_id is involved.

        Args:
            party_id (str): The unique identifier of the party.

        Returns:
            dict: {
                "success": True,
                "data": List[CaseInfo]  # List of cases involving the party (empty if none)
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (e.g. party does not exist)
            }

        Constraints:
            - party_id must exist in the system.
        """
        if party_id not in self.parties:
            return { "success": False, "error": "Party does not exist" }

        result = [
            case_info
            for case_info in self.cases.values()
            if party_id in case_info["involved_parties"]
        ]
        return { "success": True, "data": result }

    def list_cases_by_judge(self, judge_identifier: str) -> dict:
        """
        Retrieve all cases assigned to the specified judge (by judge's user ID or name).

        Args:
            judge_identifier (str): User ID or name of the judge.

        Returns:
            dict: 
              - On success: { "success": True, "data": List[CaseInfo] }
              - On failure: { "success": False, "error": str }

        Constraints:
            - Judge must exist as a User with role "judge".
            - Assigned cases are those where CaseInfo.assigned_judge matches
              the judge's user ID.
        """
        # Search for user by id or name, and ensure role is "judge"
        judge_user = None
        for user in self.users.values():
            if (user["_id"] == judge_identifier or user["name"] == judge_identifier) and user["role"].lower() == "judge":
                judge_user = user
                break

        if not judge_user:
            return { "success": False, "error": "No such judge" }

        judge_id = judge_user["_id"]
        # Assigned_judge is assumed to store the judge's user ID.
        cases = [case_info for case_info in self.cases.values() if case_info["assigned_judge"] == judge_id]

        return { "success": True, "data": cases }

    def get_party_by_id(self, party_id: str) -> dict:
        """
        Retrieve all details for a single party given their party_id.

        Args:
            party_id (str): Unique identifier of the party.

        Returns:
            dict: 
                - On success: {
                    "success": True,
                    "data": PartyInfo  # All attributes about the party
                  }
                - On failure: {
                    "success": False,
                    "error": "Party not found"
                  }

        Constraints:
            - party_id must exist in the environment.
            - No permission check required for this operation.
        """
        party = self.parties.get(party_id)
        if party is None:
            return { "success": False, "error": "Party not found" }
        return { "success": True, "data": party }

    def list_parties_in_case(self, case_number: str) -> dict:
        """
        Retrieve party details (party_id, name, role, contact_information) for all parties involved in a case.

        Args:
            case_number (str): Unique identifier of the case.

        Returns:
            dict: {
                "success": True,
                "data": List[dict]  # Each dict: {party_id, name, role, contact_information}
            }
            or
            {
                "success": False,
                "error": str  # Reason (e.g. case does not exist)
            }

        Constraints:
            - The specified case_number must exist in the system.
            - Party IDs referenced in the case must exist in self.parties (missing ones are skipped).
        """
        case_info = self.cases.get(case_number)
        if not case_info:
            return { "success": False, "error": "Case not found." }

        result = []
        for party_id in case_info.get("involved_parties", []):
            party_info = self.parties.get(party_id)
            if party_info:
                result.append({
                    "party_id": party_info["party_id"],
                    "name": party_info["name"],
                    "role": self._get_party_role_for_case(case_number, party_id),
                    "contact_information": party_info["contact_information"]
                })
        return { "success": True, "data": result }

    def get_legal_event_by_id(self, event_id: str) -> dict:
        """
        Retrieve the details of a single legal event by its event_id.

        Args:
            event_id (str): The unique identifier of the legal event.

        Returns:
            dict:
                On success:
                    {"success": True, "data": LegalEventInfo}
                If not found:
                    {"success": False, "error": "Legal event does not exist"}

        Constraints:
            - The event_id must exist in the legal_events dictionary.
        """
        legal_event = self.legal_events.get(event_id)
        if legal_event is None:
            return {"success": False, "error": "Legal event does not exist"}
        return {"success": True, "data": legal_event}

    def list_legal_events_for_case(self, case_number: str) -> dict:
        """
        Retrieve the full chronological list of legal events for a given case_number.

        Args:
            case_number (str): Identifier of the case.

        Returns:
            dict:
                - success: True, data: List[LegalEventInfo] (chronologically sorted by event date)
                - success: False, error: str (if case not found)
        Constraints:
            - The case_number must exist in the system.
            - Only legal events referenced by the case's legal_events list are included.
            - Returned in chronological order by their 'date' attribute.
        """
        if case_number not in self.cases:
            return { "success": False, "error": "Case not found" }

        case_info = self.cases[case_number]
        event_infos = [
            self.legal_events[event_id]
            for event_id in case_info.get("legal_events", [])
            if event_id in self.legal_events
        ]
        # Sort by 'date' (assuming ISO format or comparable)
        event_infos.sort(key=lambda e: e["date"])

        return { "success": True, "data": event_infos }

    def get_document_by_id(self, document_id: str) -> dict:
        """
        Retrieve metadata/details for a specific document by its document_id.

        Args:
            document_id (str): The unique identifier for the document.

        Returns:
            dict: 
                - If found: { "success": True, "data": DocumentInfo }
                - If not found: { "success": False, "error": "Document not found" }
    
        Constraints:
            - The document must exist in the system.
        """
        document = self.documents.get(document_id)
        if document is None:
            return { "success": False, "error": "Document not found" }
        return { "success": True, "data": document }

    def list_documents_for_case(self, case_number: str) -> dict:
        """
        Retrieve the list of all documents (with metadata) associated with a given case_number.

        Args:
            case_number (str): The unique identifier for the case.

        Returns:
            dict:
              - On success: { "success": True, "data": List[DocumentInfo] }
                (list empty if the case has no documents)
              - On failure: { "success": False, "error": "Case not found" }

        Constraints:
            - The case must exist in the system.
            - Only documents present in self.documents will be returned (if a case refers to a missing doc, it is ignored).
        """
        if case_number not in self.cases:
            return { "success": False, "error": "Case not found" }

        case_info = self.cases[case_number]
        result = [
            self.documents[doc_id]
            for doc_id in case_info.get("documents", [])
            if doc_id in self.documents
        ]
        return { "success": True, "data": result }

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user details for a given user ID.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo,  # User information if found
            }
            or
            {
                "success": False,
                "error": str  # If user not found
            }

        Constraints:
            - The user with the provided user_id must exist in the system.
        """
        if not user_id or user_id not in self.users:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": self.users[user_id] }

    def verify_user_permission_for_case(self, user_id: str, case_number: str, action: str) -> dict:
        """
        Check if a user has permission to view or update a given case or its documents.

        Args:
            user_id (str): User identifier (_id).
            case_number (str): Identifier for the case.
            action (str): Either "view" or "update".

        Returns:
            dict: {
                "success": True,
                "data": bool  # True if permitted, False if not permitted
            }
            or
            {
                "success": False,
                "error": str  # If the user or case does not exist, or action is invalid
            }

        Constraints:
        - The user and case must exist.
        - Only authorized users with proper permissions can view/update the case or its documents.
        - action must be "view" or "update".
        """
        # Validate action
        if action not in ("view", "update"):
            return { "success": False, "error": "Invalid action. Must be 'view' or 'update'." }
        # Validate user
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User does not exist" }
        # Validate case
        case = self.cases.get(case_number)
        if not case:
            return { "success": False, "error": "Case does not exist" }
    
        perm = user.get("permission", "")

        if action == "view":
            # Allow if user has broad or direct permission
            if perm in ("view_all", "update_all"):
                return { "success": True, "data": True }
            # If user is assigned judge
            if user_id == case.get("assigned_judge"):
                return { "success": True, "data": True }
            # For more granular permissions
            if perm == "view_case":
                return { "success": True, "data": True }
            # You could expand this rule to check party involvement, etc.

        if action == "update":
            if perm == "update_all":
                return { "success": True, "data": True }
            if user_id == case.get("assigned_judge"):
                return { "success": True, "data": True }
            if perm == "update_case":
                return { "success": True, "data": True }

        # Not permitted
        return { "success": True, "data": False }

    def search_cases_by_status(self, status: str) -> dict:
        """
        List all cases currently at the specified status.

        Args:
            status (str): The case status to search for (e.g., "Open", "Closed", "Pending").

        Returns:
            dict: {
                "success": True,
                "data": List[CaseInfo],  # List of cases with the specified status (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., invalid status argument
            }

        Constraints:
            - This operation does not enforce permission checks.
            - Status must be provided as a string.
        """
        if not isinstance(status, str) or not status.strip():
            return {"success": False, "error": "Invalid or missing status argument."}
    
        results = [
            case_info
            for case_info in self.cases.values()
            if case_info.get("status") == status
        ]

        return {"success": True, "data": results}

    def list_all_cases(self) -> dict:
        """
        Retrieve basic details for all cases in the system.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": List[CaseInfo]  # List of case info dicts (may be empty if no cases)
                }
        Notes:
            - Returns all cases currently in the system.
            - Does not require user authorization for this query operation.
        """
        all_cases = list(self.cases.values())
        return { "success": True, "data": all_cases }

    def update_case_status(self, case_number: str, new_status: str, user_id: str) -> dict:
        """
        Manually update the status of a case, if the user has necessary permissions.

        Args:
            case_number (str): Identifier of the case to update.
            new_status (str): The new status to set.
            user_id (str): Identifier of the user performing the operation.

        Returns:
            dict: {
                "success": True,
                "message": "Case status updated to <new_status>."
            }
            or
            {
                "success": False,
                "error": str  # Error message describing the failure reason.
            }

        Constraints:
            - User must exist and have permission to update case status.
            - Case must exist.
        """
        # Check if case exists
        case = self.cases.get(case_number)
        if not case:
            return {"success": False, "error": "Case not found."}
    
        # Check if user exists
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User not found."}
    
        # Check user permission
        # For this example, we assume permissions to update case status:
        # permission == 'admin' or permission == 'update_case_status'
        # role == 'judge' or 'clerk' may also have rights
        user_perm = user.get("permission", "")
        user_role = user.get("role", "")
        if (
            not self._is_case_admin_user(user)
            and user_perm not in ("admin", "update_case_status")
            and user_role not in ("judge", "clerk")
        ):
            return {"success": False, "error": "Permission denied: insufficient rights to update case status."}
    
        # Perform update
        case["status"] = new_status
        # If you want to ensure it's saved: self.cases[case_number] = case  # dicts are mutable
    
        return {
            "success": True,
            "message": f"Case status updated to {new_status}."
        }

    def create_case(
        self,
        case_number: str,
        case_type: str,
        filing_date: str,
        status: str,
        involved_parties: list,
        legal_events: list,
        documents: list,
        assigned_judge: str,
        court_location: str
    ) -> dict:
        """
        Add a new case with all required initial details.

        Args:
            case_number (str): Unique identifier for the case.
            case_type (str): Type/category of the case.
            filing_date (str): Date when the case was filed.
            status (str): Initial status of the case.
            involved_parties (list of str): List of party_ids (must exist in self.parties).
            legal_events (list of str): List of event_ids (must exist in self.legal_events); may be empty.
            documents (list of str): List of document_ids (must exist in self.documents); may be empty.
            assigned_judge (str): Judge assigned to the case.
            court_location (str): Location of the court.

        Returns:
            dict: On success:
                      {"success": True, "message": "Case <case_number> created successfully."}
                  On failure:
                      {"success": False, "error": <reason>}
        Constraints:
            - Case number must be unique.
            - All party_ids, event_ids, document_ids referenced must exist in the system.
        """
        # Enforce unique case_number
        if case_number in self.cases:
            return {"success": False, "error": "Case number already exists."}
    
        # Check all involved_parties exist
        for pid in involved_parties:
            if pid not in self.parties:
                return {"success": False, "error": f"Party ID {pid} does not exist."}
    
        # Check all legal_events exist
        for eid in legal_events:
            if eid not in self.legal_events:
                return {"success": False, "error": f"Legal event ID {eid} does not exist."}
    
        # Check all documents exist
        for did in documents:
            if did not in self.documents:
                return {"success": False, "error": f"Document ID {did} does not exist."}
    
        # Create and store the case
        self.cases[case_number] = {
            "case_number": case_number,
            "case_type": case_type,
            "filing_date": filing_date,
            "status": status,
            "involved_parties": list(involved_parties) if involved_parties else [],
            "legal_events": list(legal_events) if legal_events else [],
            "documents": list(documents) if documents else [],
            "assigned_judge": assigned_judge,
            "court_location": court_location
        }
        for party_id in involved_parties or []:
            self._case_party_roles[(case_number, party_id)] = self.parties[party_id]["role"]
        return {"success": True, "message": f"Case {case_number} created successfully."}

    def update_case_details(self, case_number: str, update_fields: dict, user_id: str) -> dict:
        """
        Edit core case information (e.g., court_location, assigned_judge, case_type, filing_date) for a given case.
    
        Args:
            case_number (str): Unique identifier for the case to update.
            update_fields (dict): Mapping of field names to updated values (editable: 'court_location', 'assigned_judge', 'case_type', 'filing_date').
            user_id (str): ID of the user attempting the update (for permission validation).

        Returns:
            dict: {
                "success": True,
                "message": "Case details updated for case <case_number>"
            }
            or:
            {
                "success": False,
                "error": str  # description of problem (not found, permission denied, invalid field, etc.)
            }

        Constraints:
            - Only authorized users with proper permissions can update case details.
            - Cannot update case_number, involved_parties, legal_events, documents, or status.
            - Case must exist; user must exist.
        """
        # Validate existence of case
        if case_number not in self.cases:
            return { "success": False, "error": "Case not found" }

        # Validate existence of user
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }

        # Permission check
        # For illustration: Allow if user.permission includes 'edit_case' or user.role in ["clerk", "judge"]
        allowed = False
        if self._is_case_admin_user(user):
            allowed = True
        elif "edit_case" in user.get("permission", ""):
            allowed = True
        elif user.get("role") in ["clerk", "judge"]:
            allowed = True
        if not allowed:
            return { "success": False, "error": "User does not have permission to edit case details" }

        # Define editable fields
        editable_fields = {"court_location", "assigned_judge", "case_type", "filing_date"}
        forbidden_fields = set(update_fields.keys()) - editable_fields

        if forbidden_fields:
            return {
                "success": False,
                "error": f"Cannot update fields: {', '.join(forbidden_fields)}"
            }

        # Update fields
        case = self.cases[case_number]
        updated = False

        for field, value in update_fields.items():
            if field in editable_fields:
                case[field] = value
                updated = True

        if not updated:
            return {
                "success": False,
                "error": "No valid fields to update"
            }

        # Optionally, update the case's entry after changes (dict reference suffices)
        return {
            "success": True,
            "message": f"Case details updated for case {case_number}"
        }

    def add_party_to_case(self, case_number: str, party_id: str, role: str) -> dict:
        """
        Assign a party to a case with a specific role.

        Args:
            case_number (str): The case to which the party is to be added.
            party_id (str): The unique ID of the party to add.
            role (str): The role of the party within this case (e.g., 'plaintiff', 'defendant', 'attorney').

        Returns:
            dict: {
                "success": True,
                "message": "Party {party_id} added to case {case_number} with role {role}."
            }
            or
            {
                "success": False,
                "error": <error_reason>
            }

        Constraints:
            - Case must exist.
            - Party must exist.
            - Party may not already be involved in the case.
            - Party must have an assigned role within the context of the case.

        Notes:
            - If PartyInfo.role is global, this update will overwrite that role,
              which may not be desired in multirole, multi-case situations; consider model extension.
        """
        if case_number not in self.cases:
            return { "success": False, "error": f"Case {case_number} does not exist." }
        if party_id not in self.parties:
            return { "success": False, "error": f"Party {party_id} does not exist." }
        case = self.cases[case_number]
        if party_id in case["involved_parties"]:
            return { "success": False, "error": f"Party {party_id} is already assigned to case {case_number}." }

        case["involved_parties"].append(party_id)
        self.cases[case_number] = case
        self._case_party_roles[(case_number, party_id)] = role

        return { "success": True,
                 "message": f"Party {party_id} added to case {case_number} with role {role}." }

    def update_party_role_in_case(self, case_number: str, party_id: str, new_role: str) -> dict:
        """
        Change the role of a party within a given case.
    
        Args:
            case_number (str): The case in which to update the party's role.
            party_id (str): The ID of the party whose role is being updated.
            new_role (str): The new role to assign within the case.
    
        Returns:
            dict: 
                If successful:
                    {
                        "success": True,
                        "message": "Party role updated in case."
                    }
                On failure:
                    {
                        "success": False,
                        "error": str
                    }
    
        Constraints:
            - The case must exist.
            - The party must exist.
            - The party must be involved in the case.
            - (Role is updated globally for this party: as per PartyInfo definition.)
        """
        if case_number not in self.cases:
            return { "success": False, "error": "Case does not exist." }
        if party_id not in self.parties:
            return { "success": False, "error": "Party does not exist." }
        if party_id not in self.cases[case_number]["involved_parties"]:
            return { "success": False, "error": "Party is not involved in the specified case." }
        self._case_party_roles[(case_number, party_id)] = new_role
        return { "success": True, "message": "Party role updated in case." }

    def remove_party_from_case(self, case_number: str, party_id: str) -> dict:
        """
        Remove a party (by party_id) from involvement in a case (by case_number).

        Args:
            case_number (str): The case from which the party is to be removed.
            party_id (str): The ID of the party to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Party <party_id> removed from case <case_number>."
            }
            or
            dict: {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The case_number must exist in the system.
            - The party_id must exist in the system.
            - The party_id must be in the involved_parties list for the case.
        """
        # Check case existence
        if case_number not in self.cases:
            return {"success": False, "error": "Case does not exist."}
        # Check party existence
        if party_id not in self.parties:
            return {"success": False, "error": "Party does not exist."}
        # Check party association with case
        if party_id not in self.cases[case_number]["involved_parties"]:
            return {
                "success": False,
                "error": f"Party {party_id} is not involved in case {case_number}."
            }

        # Remove party from involved_parties
        self.cases[case_number]["involved_parties"].remove(party_id)
        self._case_party_roles.pop((case_number, party_id), None)
        return {
            "success": True,
            "message": f"Party {party_id} removed from case {case_number}."
        }

    def create_legal_event(
        self, 
        event_id: str, 
        case_number: str, 
        date: str, 
        event_type: str, 
        description: str
    ) -> dict:
        """
        Add a new legal event to an existing case.

        Args:
            event_id (str): Unique identifier for the legal event.
            case_number (str): The case to which the event is to be added (must exist).
            date (str): The date of the legal event.
            event_type (str): The type/category of event (e.g., 'hearing', 'judgment').
            description (str): Detail/summary of the legal event.

        Returns:
            dict: {
              "success": True,
              "message": "Legal event created and linked to case."
            }
            or
            {
              "success": False,
              "error": "<reason>"
            }

        Constraints:
            - event_id must be unique.
            - case_number must exist.
            - Event is appended to case's legal_events list.
            - (If event_type should update case status, that logic can be added if specified.)
        """

        # Check: event_id unique
        if event_id in self.legal_events:
            return { "success": False, "error": "event_id already exists" }

        # Check: case_number exists
        case = self.cases.get(case_number)
        if not case:
            return { "success": False, "error": "case_number does not exist" }

        # Check: required params
        if not all([event_id, case_number, date, event_type, description]):
            return { "success": False, "error": "Missing required event field(s)" }

        # Create event
        event_info = {
            "event_id": event_id,
            "case_number": case_number,
            "date": date,
            "event_type": event_type,
            "description": description,
        }
        self.legal_events[event_id] = event_info

        # Link event to case
        case["legal_events"].append(event_id)

        # [Optional logic: If event_type affects case status, update it]
        # Not implementing status update here unless mapping is specified.

        return { "success": True, "message": "Legal event created and linked to case." }

    def update_legal_event(
        self,
        event_id: str,
        date: str = None,
        event_type: str = None,
        description: str = None,
        case_number: str = None
    ) -> dict:
        """
        Edit the details of an existing legal event.

        Args:
            event_id (str): ID of the legal event to update.
            date (str, optional): New date for the event.
            event_type (str, optional): New type for the event.
            description (str, optional): New description for the event.
            case_number (str, optional): New associated case number for the event.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Legal event <event_id> updated successfully." }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - event_id must exist in the system.
            - If updating case_number, it must exist in cases.
            - At least one updatable field must be provided.
        """
        # Check if event exists
        if event_id not in self.legal_events:
            return { "success": False, "error": "Legal event not found." }

        # Ensure at least one update argument is provided
        if all(x is None for x in [date, event_type, description, case_number]):
            return { "success": False, "error": "No updates specified." }

        legal_event = self.legal_events[event_id]
        updated_fields = []

        # Optionally update each field if provided
        if date is not None:
            legal_event["date"] = date
            updated_fields.append("date")
        if event_type is not None:
            legal_event["event_type"] = event_type
            updated_fields.append("event_type")
        if description is not None:
            legal_event["description"] = description
            updated_fields.append("description")
        if case_number is not None:
            if case_number not in self.cases:
                return { "success": False, "error": "Target case does not exist." }
            # Update in the event
            prev_case_number = legal_event["case_number"]
            legal_event["case_number"] = case_number
            # Also need to move the event reference between case objects
            # Remove from previous
            if event_id in self.cases[prev_case_number]["legal_events"]:
                self.cases[prev_case_number]["legal_events"].remove(event_id)
            # Add to new case
            if event_id not in self.cases[case_number]["legal_events"]:
                self.cases[case_number]["legal_events"].append(event_id)
            updated_fields.append("case_number")

        self.legal_events[event_id] = legal_event  # Re-save to be explicit

        return {
            "success": True,
            "message": f"Legal event {event_id} updated successfully ({', '.join(updated_fields)})."
        }

    def remove_legal_event(self, event_id: str) -> dict:
        """
        Delete a legal event from the system and update case status if necessary.

        Args:
            event_id (str): The ID of the legal event to remove.

        Returns:
            dict: {
                "success": True,
                "message": Description of the change,
            }
            OR
            {
                "success": False,
                "error": Error description,
            }

        Constraints:
          - Legal event must exist.
          - Must be associated with a valid case.
          - Must update the status of the case to reflect the now-latest (by date) event,
            or to "No Events" if none remain.
        """
        # Check if legal event exists
        if event_id not in self.legal_events:
            return {"success": False, "error": "Legal event ID does not exist."}

        event = self.legal_events[event_id]
        case_number = event["case_number"]

        # Check if the associated case exists
        if case_number not in self.cases:
            return {"success": False, "error": "Associated case not found."}

        case = self.cases[case_number]
        # Remove event_id from the case's legal_events list (if present)
        if event_id in case["legal_events"]:
            case["legal_events"].remove(event_id)

        # Remove the legal event itself
        del self.legal_events[event_id]

        # Update case status
        if case["legal_events"]:
            # Get all remaining events for the case
            remaining_event_ids = case["legal_events"]
            # Reconstruct and sort events by date to find the latest
            def event_date(ev):
                # Assumes ISO-8601 date string (lexicographical order == date order)
                return self.legal_events[ev]["date"]
            # Find the event_id with max date
            latest_event_id = max(remaining_event_ids, key=event_date)
            latest_event = self.legal_events[latest_event_id]
            # For status, system rule is to use event_type or description (here, event_type)
            case["status"] = latest_event["event_type"]
            status_message = f"Case status updated to latest event_type: {latest_event['event_type']}."
        else:
            # No legal events remain; set status to default
            case["status"] = "No Events"
            status_message = "Case status set to 'No Events' as no legal events remain."

        return {
            "success": True,
            "message": f"Legal event '{event_id}' removed. {status_message}"
        }

    def add_document_to_case(
        self,
        document_id: str,
        case_number: str,
        file_name: str,
        file_type: str,
        upload_date: str,
        access_level: str
    ) -> dict:
        """
        Upload or register a document and associate it with an existing case.

        Args:
            document_id (str): Unique ID for the document.
            case_number (str): Case number to associate the document with. Must exist.
            file_name (str): Name of the document file.
            file_type (str): File type (format, e.g., pdf).
            upload_date (str): Date the document is uploaded (format YYYY-MM-DD or ISO).
            access_level (str): Access restriction of the document.

        Returns:
            dict:
                Success: { "success": True, "message": "Document added to case." }
                Failure: { "success": False, "error": "<reason>" }

        Constraints:
            - The document_id must be unique (not already present in self.documents).
            - The case_number must reference an existing case.
            - All required fields must be present and non-empty.
            - The document is then added and linked to the case's documents list.
        """
        # Check required fields
        if not all([document_id, case_number, file_name, file_type, upload_date, access_level]):
            return {"success": False, "error": "All document attributes must be provided and non-empty."}

        # Check document_id uniqueness
        if document_id in self.documents:
            return {"success": False, "error": "Document ID already exists."}

        # Check that case_number exists
        if case_number not in self.cases:
            return {"success": False, "error": "Associated case does not exist."}

        # Create the document entry
        doc_info: DocumentInfo = {
            "document_id": document_id,
            "case_number": case_number,
            "file_name": file_name,
            "file_type": file_type,
            "upload_date": upload_date,
            "access_level": access_level,
        }
        self.documents[document_id] = doc_info

        # Add document ID to the case's documents list
        if "documents" not in self.cases[case_number]:
            self.cases[case_number]["documents"] = []
        if document_id not in self.cases[case_number]["documents"]:
            self.cases[case_number]["documents"].append(document_id)

        return {"success": True, "message": "Document added to case."}

    def update_document_metadata(
        self,
        user_id: str,
        document_id: str,
        new_metadata: dict
    ) -> dict:
        """
        Edit the metadata (file_name, file_type, access_level, upload_date) for a document.
        Only authorized users can perform this action.

        Args:
            user_id (str): ID of the user requesting the update.
            document_id (str): ID of the target document.
            new_metadata (dict): Dictionary of metadata fields to update (allowed: file_name, file_type, access_level, upload_date).

        Returns:
            dict: {
                "success": True,
                "message": "Document metadata updated successfully"
            }
            or {
                "success": False,
                "error": str
            }

        Constraints:
            - Only users with sufficient permission can update.
            - Only certain fields are updatable.
            - Document and user must exist.
        """
        # 1. Check user existence
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }
    
        # 2. Check document existence
        document = self.documents.get(document_id)
        if not document:
            return { "success": False, "error": "Document not found" }
    
        # 3. Permission check (example: allow if user is "admin" or has "edit_document" in permission)
        allowed_roles = {'admin', 'clerk', 'judge'}  # Example roles allowed
        allowed_permissions = {'edit_document', 'admin'}
        user_role = user.get("role", "")
        user_perm = user.get("permission", "")

        # For simplicity, check if user is admin OR has edit_document permission OR is a judge/clerk
        if (user_role not in allowed_roles) and (user_perm not in allowed_permissions):
            return { "success": False, "error": "Permission denied" }

        limit = self.document_update_limits.get(user_id)
        if limit is not None:
            used = self.document_update_usage.get(user_id, 0)
            if used >= int(limit):
                return {
                    "success": False,
                    "error": "Administrative session token has expired for document metadata updates"
                }

        # 4. Validate updatable fields
        editable_fields = {"file_name", "file_type", "access_level", "upload_date"}
        invalid_fields = [k for k in new_metadata if k not in editable_fields]
        if invalid_fields:
            return { "success": False, "error": f"Invalid metadata fields: {', '.join(invalid_fields)}" }
        if not any(k in editable_fields for k in new_metadata):
            return { "success": False, "error": "No valid fields to update" }

        # 5. Perform update
        for k, v in new_metadata.items():
            if k in editable_fields:
                document[k] = v

        self.documents[document_id] = document  # Save the updated document
        if limit is not None:
            self.document_update_usage[user_id] = self.document_update_usage.get(user_id, 0) + 1

        return { "success": True, "message": "Document metadata updated successfully" }

    def remove_document_from_case(self, case_number: str, document_id: str, user_id: str) -> dict:
        """
        Unlink and delete a document from a specific case after verifying permissions.

        Args:
            case_number (str): The case from which the document will be removed.
            document_id (str): The document to remove/unlink.
            user_id (str): The user requesting the operation (for permission check).

        Returns:
            dict: {
                "success": True,
                "message": "Document <document_id> removed from case <case_number>"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The specified case and document must exist.
            - Document must be associated with the case.
            - Only authorized users can modify case documents.
            - On success, the document is unlinked from the case and deleted from the system.
        """
        # Check user exists and permissions
        user_info = self.users.get(user_id)
        if not user_info:
            return {"success": False, "error": "User does not exist"}
        if user_info.get("permission") not in ["admin", "clerk", "judge"]:
            # You may want to adjust permission logic as per your roles
            return {"success": False, "error": "User does not have permission to remove documents"}

        if case_number not in self.cases:
            return {"success": False, "error": "Case does not exist"}

        case_info = self.cases[case_number]

        if document_id not in self.documents:
            return {"success": False, "error": "Document does not exist"}

        if document_id not in case_info["documents"]:
            return {"success": False, "error": "Document is not associated with the specified case"}

        # Remove document_id from case's documents list
        case_info["documents"].remove(document_id)
        self.cases[case_number] = case_info  # Not strictly necessary but preserves intent

        # Delete the document from system
        del self.documents[document_id]

        return {
            "success": True,
            "message": f"Document {document_id} removed from case {case_number}"
        }

    def create_user(self, _id: str, name: str, role: str, permission: str) -> dict:
        """
        Register a new user in the court management system.

        Args:
            _id (str): Unique user identifier.
            name (str): User's full name.
            role (str): User's system role (e.g. clerk, judge, attorney).
            permission (str): User's permission level/descriptor.

        Returns:
            dict: {
                "success": True,
                "message": "User created successfully"
            }
            or
            {
                "success": False,
                "error": "User with this ID already exists" or another error reason
            }

        Constraints:
            - _id must be unique among all users.
            - All fields must be non-empty strings.
        """
        if not (_id and name and role and permission):
            return {"success": False, "error": "Missing or empty required user fields"}

        if _id in self.users:
            return {"success": False, "error": "User with this ID already exists"}

        # Prepare user info
        user_info: UserInfo = {
            "_id": _id,
            "name": name,
            "role": role,
            "permission": permission
        }
        self.users[_id] = user_info

        return {"success": True, "message": "User created successfully"}

    def update_user_permission(self, user_id: str, by_user_id: str, new_permission: str = None, new_role: str = None) -> dict:
        """
        Change the permission level and/or role of a system user.

        Args:
            user_id (str): The user whose permission or role is to be updated.
            by_user_id (str): The user performing the operation (for permission checks).
            new_permission (str, optional): The new permission value for the user.
            new_role (str, optional): The new role for the user.

        Returns:
            dict: {
                "success": True,
                "message": "User permission and/or role updated successfully."
            }
            or
            {
                "success": False,
                "error": str  # Failure reason
            }

        Constraints:
            - Acting user must exist and have admin or equivalent level permissions.
            - Target user must exist.
            - At least one of new_permission or new_role must be specified.
        """

        # Permission check: acting user must exist
        acting_user = self.users.get(by_user_id)
        if not acting_user:
            return {"success": False, "error": "Acting user not found."}

        # Permission check: only admins or users with explicit permission can update users
        if acting_user.get("role") != "admin" and acting_user.get("permission") != "admin":
            return {"success": False, "error": "Permission denied. Only admins can update user permissions or roles."}

        # Target user exists?
        user_info = self.users.get(user_id)
        if not user_info:
            return {"success": False, "error": "Target user not found."}

        # At least one field to update
        if new_permission is None and new_role is None:
            return {"success": False, "error": "No updates specified. Provide new_permission and/or new_role."}

        updated = False
        if new_permission is not None:
            user_info["permission"] = new_permission
            updated = True

        if new_role is not None:
            user_info["role"] = new_role
            updated = True

        if updated:
            self.users[user_id] = user_info
            return {"success": True, "message": "User permission and/or role updated successfully."}
        else:
            # This branch should not be reached due to previous checks
            return {"success": False, "error": "No update performed."}

    def delete_case(self, case_number: str, user_id: str) -> dict:
        """
        Remove a legal case from the system. Requires admin-level privilege.

        Args:
            case_number (str): The case_number of the case to delete.
            user_id (str): The ID of the user attempting the operation.

        Returns:
            dict: 
                On success: { "success": True, "message": "Case X deleted." }
                On failure: { "success": False, "error": str }
    
        Constraints:
            - Only users with admin role/permission can delete cases.
            - All associated legal events and documents are also removed from the system.
            - Fails if case_number or user_id are invalid or permission is insufficient.
        """
        # Check if user exists
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User not found."}
        # Check permission (assume 'admin' is indicated either by role or permission)
        if not (user.get('role', '').lower() == 'admin' or user.get('permission', '').lower() == 'admin'):
            return {"success": False, "error": "Permission denied: admin required."}
        # Check if case exists
        case = self.cases.get(case_number)
        if not case:
            return {"success": False, "error": "Case not found."}

        # Remove associated legal events
        for event_id in case.get("legal_events", []):
            if event_id in self.legal_events:
                del self.legal_events[event_id]
        # Remove associated documents
        for doc_id in case.get("documents", []):
            if doc_id in self.documents:
                del self.documents[doc_id]
        # Unlink this case from parties (not strictly necessary if parties can belong to multiple cases)
        # No action needed unless parties store explicit references.
        # Finally, remove the case
        del self.cases[case_number]

        return {"success": True, "message": f"Case {case_number} deleted."}


class CourtCaseManagementSystem(BaseEnv):
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
        env._case_party_roles = {}
        for case_number, case_info in getattr(env, "cases", {}).items():
            for party_id in case_info.get("involved_parties", []):
                party = getattr(env, "parties", {}).get(party_id)
                if party is not None:
                    env._case_party_roles[(case_number, party_id)] = party.get("role", "")

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

    def get_case_by_number(self, **kwargs):
        return self._call_inner_tool('get_case_by_number', kwargs)

    def get_case_status(self, **kwargs):
        return self._call_inner_tool('get_case_status', kwargs)

    def list_cases_by_party(self, **kwargs):
        return self._call_inner_tool('list_cases_by_party', kwargs)

    def list_cases_by_judge(self, **kwargs):
        return self._call_inner_tool('list_cases_by_judge', kwargs)

    def get_party_by_id(self, **kwargs):
        return self._call_inner_tool('get_party_by_id', kwargs)

    def list_parties_in_case(self, **kwargs):
        return self._call_inner_tool('list_parties_in_case', kwargs)

    def get_legal_event_by_id(self, **kwargs):
        return self._call_inner_tool('get_legal_event_by_id', kwargs)

    def list_legal_events_for_case(self, **kwargs):
        return self._call_inner_tool('list_legal_events_for_case', kwargs)

    def get_document_by_id(self, **kwargs):
        return self._call_inner_tool('get_document_by_id', kwargs)

    def list_documents_for_case(self, **kwargs):
        return self._call_inner_tool('list_documents_for_case', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def verify_user_permission_for_case(self, **kwargs):
        return self._call_inner_tool('verify_user_permission_for_case', kwargs)

    def search_cases_by_status(self, **kwargs):
        return self._call_inner_tool('search_cases_by_status', kwargs)

    def list_all_cases(self, **kwargs):
        return self._call_inner_tool('list_all_cases', kwargs)

    def update_case_status(self, **kwargs):
        return self._call_inner_tool('update_case_status', kwargs)

    def create_case(self, **kwargs):
        return self._call_inner_tool('create_case', kwargs)

    def update_case_details(self, **kwargs):
        return self._call_inner_tool('update_case_details', kwargs)

    def add_party_to_case(self, **kwargs):
        return self._call_inner_tool('add_party_to_case', kwargs)

    def update_party_role_in_case(self, **kwargs):
        return self._call_inner_tool('update_party_role_in_case', kwargs)

    def remove_party_from_case(self, **kwargs):
        return self._call_inner_tool('remove_party_from_case', kwargs)

    def create_legal_event(self, **kwargs):
        return self._call_inner_tool('create_legal_event', kwargs)

    def update_legal_event(self, **kwargs):
        return self._call_inner_tool('update_legal_event', kwargs)

    def remove_legal_event(self, **kwargs):
        return self._call_inner_tool('remove_legal_event', kwargs)

    def add_document_to_case(self, **kwargs):
        return self._call_inner_tool('add_document_to_case', kwargs)

    def update_document_metadata(self, **kwargs):
        return self._call_inner_tool('update_document_metadata', kwargs)

    def remove_document_from_case(self, **kwargs):
        return self._call_inner_tool('remove_document_from_case', kwargs)

    def create_user(self, **kwargs):
        return self._call_inner_tool('create_user', kwargs)

    def update_user_permission(self, **kwargs):
        return self._call_inner_tool('update_user_permission', kwargs)

    def delete_case(self, **kwargs):
        return self._call_inner_tool('delete_case', kwargs)
