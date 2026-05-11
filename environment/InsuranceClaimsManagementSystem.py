# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import uuid
from datetime import datetime
from typing import Optional, List, Dict



class ClaimInfo(TypedDict):
    claim_id: str
    policyholder_id: str
    date_filed: str       # ISO date string
    status: str
    claim_type: str
    claim_amount: float
    supporting_documents: List[str]   # List of document_ids
    interactions: List[str]           # List of interaction_ids
    assigned_adjuster_id: str
    payout_amount: float
    resolution_date: str  # ISO date string

class PolicyholderInfo(TypedDict):
    policyholder_id: str
    name: str
    contact_info: str
    policy_num: str

class DocumentInfo(TypedDict):
    document_id: str
    claim_id: str
    document_type: str
    upload_date: str          # ISO date string
    file_url: str

class InteractionInfo(TypedDict):
    interaction_id: str
    claim_id: str
    date: str                 # ISO date string
    interaction_type: str
    notes: str
    participant_id: str

class AdjusterInfo(TypedDict):
    adjuster_id: str
    name: str
    contact_info: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Claims: {claim_id: ClaimInfo}
        self.claims: Dict[str, ClaimInfo] = {}

        # Policyholders: {policyholder_id: PolicyholderInfo}
        self.policyholders: Dict[str, PolicyholderInfo] = {}

        # Documents: {document_id: DocumentInfo}
        self.documents: Dict[str, DocumentInfo] = {}

        # Interactions: {interaction_id: InteractionInfo}
        self.interactions: Dict[str, InteractionInfo] = {}

        # Adjusters: {adjuster_id: AdjusterInfo}
        self.adjusters: Dict[str, AdjusterInfo] = {}

        # --- Constraints ---
        # - Each claim_id must be unique.
        # - Status values must be from a defined set (e.g., "Filed", "Under Investigation", "Approved", "Denied", "Paid Out", etc.).
        # - Each claim is associated with exactly one policyholder.
        # - Supporting documents are linked to claims via claim_id.
        # - Interactions must be timestamped and assigned to claims.
        # - Only authorized users (e.g., policyholder or admins) may access or update claim information.

    def get_claim_by_id(self, claim_id: str) -> dict:
        """
        Retrieve full details of a claim using its unique claim_id.

        Args:
            claim_id (str): Unique identifier of the insurance claim.

        Returns:
            dict: 
                On success: { "success": True, "data": <ClaimInfo> }
                On failure: { "success": False, "error": "Claim not found" }

        Constraints:
            - claim_id must exist in the claims registry.
        """
        claim_info = self.claims.get(claim_id)
        if not claim_info:
            return { "success": False, "error": "Claim not found" }
        return { "success": True, "data": claim_info }

    def get_claim_status(self, claim_id: str) -> dict:
        """
        Query the current status of a claim by claim_id.

        Args:
            claim_id (str): The unique identifier of the claim.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": {
                            "claim_id": str,
                            "status": str
                        }
                    }
                On failure (claim does not exist):
                    {
                        "success": False,
                        "error": "Claim not found"
                    }
        Constraints:
            - The provided claim_id must exist in the system.
        """
        claim_info = self.claims.get(claim_id)
        if not claim_info:
            return { "success": False, "error": "Claim not found" }
        return {
            "success": True,
            "data": {
                "claim_id": claim_id,
                "status": claim_info["status"]
            }
        }

    def list_claims_by_policyholder(self, policyholder_id: str) -> dict:
        """
        Retrieve all claims filed by the specified policyholder.

        Args:
            policyholder_id (str): The ID of the policyholder.

        Returns:
            dict: {
                "success": True,
                "data": List[ClaimInfo]  # List of ClaimInfo filed by the policyholder (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Error message, e.g., "Policyholder not found"
            }

        Constraints:
            - Only existing policyholders are valid.
            - Each claim is associated with exactly one policyholder.
        """
        if policyholder_id not in self.policyholders:
            return {"success": False, "error": "Policyholder not found"}

        claims_list = [
            claim_info for claim_info in self.claims.values()
            if claim_info["policyholder_id"] == policyholder_id
        ]
        return {"success": True, "data": claims_list}

    def get_policyholder_by_id(self, policyholder_id: str) -> dict:
        """
        Retrieve details of a policyholder given their policyholder_id.

        Args:
            policyholder_id (str): The unique identifier of the policyholder.

        Returns:
            dict:
                On success: { "success": True, "data": PolicyholderInfo }
                On error: { "success": False, "error": "Policyholder not found" }

        Constraints:
            - The given policyholder_id must exist in the system.
        """
        policyholder = self.policyholders.get(policyholder_id)
        if not policyholder:
            return { "success": False, "error": "Policyholder not found" }
        return { "success": True, "data": policyholder }

    def get_documents_for_claim(self, claim_id: str) -> dict:
        """
        List all supporting documents (with metadata) associated with the given claim.

        Args:
            claim_id (str): The unique identifier of the claim.

        Returns:
            dict: {
                "success": True,
                "data": List[DocumentInfo],  # List of supporting documents (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., claim not found)
            }

        Constraints:
            - claim_id must exist in the system.
            - Documents are those listed in the claim's supporting_documents field
              and present in the system's document registry.
        """
        if claim_id not in self.claims:
            return { "success": False, "error": "Claim not found" }

        doc_ids = self.claims[claim_id]["supporting_documents"]
        document_list = [
            self.documents[doc_id]
            for doc_id in doc_ids
            if doc_id in self.documents
        ]
        return { "success": True, "data": document_list }

    def get_document_by_id(self, document_id: str) -> dict:
        """
        Retrieve metadata and file URL for a supporting document by document_id.

        Args:
            document_id (str): Unique identifier of the supporting document.

        Returns:
            dict:
                Success:
                    {"success": True, "data": DocumentInfo}
                Failure:
                    {"success": False, "error": "Document not found."}

        Constraints:
            - The document_id must exist in the system.
        """
        doc = self.documents.get(document_id)
        if doc is None:
            return {"success": False, "error": "Document not found."}
        return {"success": True, "data": doc}

    def get_interactions_for_claim(self, claim_id: str) -> dict:
        """
        List all interactions (communications or actions) linked to a given claim.

        Args:
            claim_id (str): The unique ID of the claim.

        Returns:
            dict: {
                "success": True,
                "data": List[InteractionInfo]
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The claim must exist.
            - The returned interactions must exist in self.interactions.
        """
        claim = self.claims.get(claim_id)
        if not claim:
            return { "success": False, "error": "Claim not found" }

        interaction_ids = claim.get("interactions", [])
        interactions = [
            self.interactions[iid]
            for iid in interaction_ids
            if iid in self.interactions
        ]
        return { "success": True, "data": interactions }

    def get_interaction_by_id(self, interaction_id: str) -> dict:
        """
        Retrieve details of a single interaction by its ID.

        Args:
            interaction_id (str): The unique identifier of the interaction to retrieve.

        Returns:
            dict:
                If success:
                    {
                        "success": True,
                        "data": InteractionInfo
                    }
                If failure (interaction not found):
                    {
                        "success": False,
                        "error": "Interaction not found"
                    }
        Constraints:
            - interaction_id must exist in the system.
        """
        interaction = self.interactions.get(interaction_id)
        if interaction is None:
            return {"success": False, "error": "Interaction not found"}
        return {"success": True, "data": interaction}

    def get_adjuster_by_id(self, adjuster_id: str) -> dict:
        """
        Retrieve details about an adjuster by their unique adjuster_id.

        Args:
            adjuster_id (str): The unique identifier for the adjuster.

        Returns:
            dict:
                - On success: { "success": True, "data": AdjusterInfo }
                - On failure: { "success": False, "error": str }
        Constraints:
            - adjuster_id must exist in the system.
        """
        adjuster = self.adjusters.get(adjuster_id)
        if not adjuster:
            return {"success": False, "error": "Adjuster ID not found"}
        return {"success": True, "data": adjuster}

    def get_claims_by_status(self, status: str) -> dict:
        """
        Retrieve all claims that match a specific status value.

        Args:
            status (str): The desired claim status (must be one of the allowed statuses).

        Returns:
            dict: {
                "success": True,
                "data": List[ClaimInfo]  # May be empty if no matches
            }
            or
            {
                "success": False,
                "error": str
            }
        Constraints:
            - Status value must be from the defined set.
        """
        # Define allowed status values (as per constraint guidelines)
        allowed_statuses = {
            "Filed", "Under Investigation", "Under Review", "Approved", "Denied", "Paid Out"
        }

        if status not in allowed_statuses:
            return {
                "success": False,
                "error": "Invalid claim status."
            }

        matching_claims = [
            claim_info for claim_info in self.claims.values()
            if claim_info["status"] == status
        ]

        return {
            "success": True,
            "data": matching_claims
        }

    def check_user_authorization_for_claim(self, claim_id: str, user_id: str, user_role: str) -> dict:
        """
        Determine if a user (policyholder or admin) is authorized to access/modify claim data.

        Args:
            claim_id (str): The claim to check access for.
            user_id (str): The unique identifier of the user.
            user_role (str): The user's role ("policyholder" or "admin").

        Returns:
            dict: 
                On success: { "success": True, "authorized": True/False }
                On error:   { "success": False, "error": "<reason>" }

        Constraints:
            - Admin can always access/modify.
            - Policyholder can access only if they own the claim.
            - Invalid roles or missing claim handled as failure.
        """
        # Check claim existence
        claim = self.claims.get(claim_id)
        if claim is None:
            return { "success": False, "error": "Claim does not exist" }

        # Normalize user_role for checking
        if user_role == "admin":
            return { "success": True, "authorized": True }
        elif user_role == "policyholder":
            if claim["policyholder_id"] == user_id:
                return { "success": True, "authorized": True }
            else:
                return { "success": True, "authorized": False }
        else:
            return { "success": False, "error": "Invalid user role" }

    def get_claim_history(self, claim_id: str) -> dict:
        """
        Return the sequence of status changes (if tracked) and all interactions for a given claim.
    
        Args:
            claim_id (str): The unique identifier of the claim to retrieve history for.
    
        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": {
                            "status_changes": List[dict],   # Each dict with at least status and date
                            "interactions": List[InteractionInfo]
                        }
                    }
                On failure:
                    {
                        "success": False,
                        "error": str
                    }
    
        Constraints:
            - claim_id must exist.
            - Interactions should be sorted by date ascending.
            - Status change sequence may be limited to first (date_filed), last (resolution_date), and current status if no full log is available.
        """
        claim = self.claims.get(claim_id)
        if claim is None:
            return {"success": False, "error": "Claim not found"}

        # Status change history: assuming only initial and resolution (no audit log of each change)
        status_changes = []
        if claim.get("date_filed"):
            status_changes.append({
                "status": "Filed",
                "date": claim["date_filed"]
            })
        # If claim is resolved (resolution_date set), record that status
        if claim.get("resolution_date"):
            # Determine resolved status
            resolved_status = claim.get("status", "Resolved")
            status_changes.append({
                "status": resolved_status,
                "date": claim["resolution_date"]
            })
        else:
            # Only current status (not yet resolved)
            if claim.get("status"):
                status_changes.append({
                    "status": claim["status"],
                    "date": None    # Unknown when status changed, so set None
                })

        # Interactions
        interaction_ids = claim.get("interactions", [])
        interactions_list = []
        for iid in interaction_ids:
            interaction = self.interactions.get(iid)
            if interaction:
                interactions_list.append(interaction)
        # Sort interactions by date
        interactions_list.sort(key=lambda x: x.get("date", ""))

        return {
            "success": True,
            "data": {
                "status_changes": status_changes,
                "interactions": interactions_list
            }
        }


    def submit_new_claim(
        self,
        policyholder_id: str,
        claim_type: str,
        claim_amount: float,
        date_filed: Optional[str] = None,
        initial_supporting_documents: Optional[List[str]] = None,
        initial_interactions: Optional[List[str]] = None
    ) -> dict:
        """
        File a new insurance claim.
        Creates a unique claim_id, sets initial status to 'Filed', and links to the specified policyholder.

        Args:
            policyholder_id (str): Existing policyholder's ID filing the claim.
            claim_type (str): Type/category of claim (e.g., 'Auto', 'Home').
            claim_amount (float): Amount being claimed.
            date_filed (Optional[str]): Filing date (ISO format). Defaults to current date if not provided.
            initial_supporting_documents (Optional[List[str]]): List of existing document_ids to link (optional, usually empty).
            initial_interactions (Optional[List[str]]): List of existing interaction_ids to link (optional, usually empty).

        Returns:
            dict:
                On success: {
                    "success": True,
                    "message": "Claim submitted",
                    "claim_id": <generated_claim_id>
                }
                On failure: {
                    "success": False,
                    "error": <reason>
                }

        Constraints:
            - policyholder_id must exist in the system.
            - claim_id is unique (auto-generated).
            - Initializes status to 'Filed'.
        """
        # Check that policyholder exists
        if policyholder_id not in self.policyholders:
            return {"success": False, "error": "Policyholder does not exist"}

        # Generate a unique claim_id
        new_claim_id = str(uuid.uuid4())
        while new_claim_id in self.claims:
            new_claim_id = str(uuid.uuid4())

        # Use provided date_filed or current date in ISO format
        if date_filed is None:
            date_filed = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        # Safe defaults for optional lists
        documents = initial_supporting_documents if initial_supporting_documents else []
        interactions = initial_interactions if initial_interactions else []

        new_claim: ClaimInfo = {
            "claim_id": new_claim_id,
            "policyholder_id": policyholder_id,
            "date_filed": date_filed,
            "status": "Filed",
            "claim_type": claim_type,
            "claim_amount": claim_amount,
            "supporting_documents": documents,
            "interactions": interactions,
            "assigned_adjuster_id": "",
            "payout_amount": 0.0,
            "resolution_date": ""
        }
        self.claims[new_claim_id] = new_claim
        return {"success": True, "message": "Claim submitted", "claim_id": new_claim_id}

    def update_claim_status(self, claim_id: str, new_status: str) -> dict:
        """
        Modify the status of an existing claim, provided the new status is valid.

        Args:
            claim_id (str): Unique identifier of the claim to update.
            new_status (str): The status to set ("Filed", "Under Investigation", 
                              "Approved", "Denied", "Paid Out", etc.)

        Returns:
            dict: {
                "success": True,
                "message": str
            } 
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Claim must exist (claim_id in system).
            - new_status must be in the defined set of valid statuses.
            - Only modifies the status (no audit trail, timestamp, or auth handled here).
        """
        VALID_STATUSES = ["Filed", "Under Investigation", "Under Review", "Approved", "Denied", "Paid Out"]

        if claim_id not in self.claims:
            return { "success": False, "error": "Claim does not exist" }
    
        if new_status not in VALID_STATUSES:
            return { "success": False, "error": f"Invalid status '{new_status}'" }

        self.claims[claim_id]["status"] = new_status
        return { "success": True, "message": f"Claim status updated to {new_status}" }

    def update_claim_info(self, claim_id: str, updates: dict) -> dict:
        """
        Change editable fields (e.g., claim_type, claim_amount, payout_amount) of an existing claim.
        Immutable fields such as claim_id, policyholder_id, date_filed, assigned_adjuster_id, status, and resolution_date cannot be updated.

        Args:
            claim_id (str): The claim to update.
            updates (dict): Dictionary of field: new_value pairs to update.

        Returns:
            dict:
              - On success: 
                    { "success": True, "message": "Claim <claim_id> updated successfully" }
              - On failure: 
                    { "success": False, "error": "reason" }

        Constraints:
        - Only editable fields can be updated.
        - If claim_id not found, report error.
        - Fields with invalid values (e.g., negative claim_amount) return error.
        - Does not perform detailed authorization check (could be added by passing user context).
        """
        # Define immutable fields
        IMMUTABLE_FIELDS = {
            "claim_id", "policyholder_id", "date_filed",
            "assigned_adjuster_id", "status", "resolution_date",
            "supporting_documents", "interactions"
        }

        if claim_id not in self.claims:
            return { "success": False, "error": "Claim not found" }

        claim = self.claims[claim_id]
        # Only update fields present in ClaimInfo and not immutable
        editable_fields = set(claim.keys()) - IMMUTABLE_FIELDS

        # Check for illegal fields in updates
        illegal_fields = set(updates.keys()) - editable_fields
        if illegal_fields:
            return { "success": False, "error": f"Fields not editable: {', '.join(illegal_fields)}" }

        # Validate values and perform updates
        for key, value in updates.items():
            if key == "claim_amount" or key == "payout_amount":
                if not isinstance(value, (int, float)) or value < 0:
                    return { "success": False, "error": f"{key} must be a non-negative number" }
                claim[key] = float(value)
            elif key == "claim_type":
                if not isinstance(value, str) or not value:
                    return { "success": False, "error": "claim_type must be a non-empty string" }
                claim[key] = value
            else:
                # For other fields, accept the update as-is
                claim[key] = value

        self.claims[claim_id] = claim
        return { "success": True, "message": f"Claim {claim_id} updated successfully" }

    def assign_adjuster_to_claim(self, claim_id: str, adjuster_id: str) -> dict:
        """
        Assign or change the adjuster responsible for a specific claim.

        Args:
            claim_id (str): The unique identifier of the claim to update.
            adjuster_id (str): The adjuster's unique identifier to assign to the claim.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Adjuster assigned to claim <claim_id> successfully." }
                On failure:
                    { "success": False, "error": <error_reason> }

        Constraints:
            - claim_id must refer to an existing claim.
            - adjuster_id must refer to an existing adjuster.
            - Only updates the 'assigned_adjuster_id' field for the claim.
        """
        if claim_id not in self.claims:
            return { "success": False, "error": f"Claim {claim_id} does not exist." }
        if adjuster_id not in self.adjusters:
            return { "success": False, "error": f"Adjuster {adjuster_id} does not exist." }

        self.claims[claim_id]["assigned_adjuster_id"] = adjuster_id
        return {
            "success": True,
            "message": f"Adjuster assigned to claim {claim_id} successfully."
        }

    def add_supporting_document_to_claim(
        self,
        claim_id: str,
        document_id: str,
        document_type: str,
        upload_date: str,
        file_url: str,
        user_id: str
    ) -> dict:
        """
        Upload a new supporting document and link it to the specified claim.

        Args:
            claim_id (str): The ID of the claim to attach the document to.
            document_id (str): A unique identifier for the new document.
            document_type (str): Type/category of the document (e.g., 'photo', 'report').
            upload_date (str): The upload date as an ISO date string.
            file_url (str): URL/path to the uploaded file.
            user_id (str): The ID of the user attempting to add the document.

        Returns:
            dict: {
                "success": True,
                "message": "Document added and linked to claim successfully."
            }
            or
            {
                "success": False,
                "error": str  # Description of the error
            }

        Constraints:
            - Claim must exist.
            - document_id must be unique.
            - Only authorized users may add documents to the claim.
            - The new document's claim_id field must match the claim,
              and it will be linked in the claim's supporting_documents list.
        """
        # Check if claim exists
        if claim_id not in self.claims:
            return {"success": False, "error": "Claim does not exist."}

        # Check if document_id is unique
        if document_id in self.documents:
            return {"success": False, "error": "Document ID already exists."}

        claim = self.claims[claim_id]
        authorized = (user_id == "admin" or claim.get("policyholder_id") == user_id)
        if not authorized:
            return {"success": False, "error": "User not authorized to add document to this claim."}

        # Create new document
        new_document: DocumentInfo = {
            "document_id": document_id,
            "claim_id": claim_id,
            "document_type": document_type,
            "upload_date": upload_date,
            "file_url": file_url
        }
        self.documents[document_id] = new_document

        # Link document to claim's supporting_documents list
        if "supporting_documents" not in claim or claim["supporting_documents"] is None:
            claim["supporting_documents"] = []
        claim["supporting_documents"].append(document_id)

        return {
            "success": True,
            "message": "Document added and linked to claim successfully."
        }

    def remove_supporting_document_from_claim(self, claim_id: str, document_id: str) -> dict:
        """
        Detach a supporting document from a claim.

        Args:
            claim_id (str): The unique ID of the claim.
            document_id (str): The ID of the document to un-link from the claim.

        Returns:
            dict:
                - On success: { "success": True, "message": "Document detached from claim." }
                - On failure: { "success": False, "error": <error_message> }

        Constraints:
            - The claim and document must both exist.
            - The document must be listed in the claim's supporting_documents.
            - The document's claim_id must match the claim_id.
            - Only detaches the document reference from the claim; does not delete the document object.
        """
        if claim_id not in self.claims:
            return { "success": False, "error": "Claim does not exist." }
        if document_id not in self.documents:
            return { "success": False, "error": "Document does not exist." }
        claim = self.claims[claim_id]
        doc = self.documents[document_id]
        if document_id not in claim["supporting_documents"]:
            return { "success": False, "error": "Document is not attached to the claim." }
        if doc["claim_id"] != claim_id:
            return { "success": False, "error": "Document's claim_id does not match the specified claim." }

        # Remove document_id from supporting_documents
        claim["supporting_documents"].remove(document_id)
        # (Optionally update document['claim_id'] to '' or None, but not specified)
        return { "success": True, "message": "Document detached from claim." }

    def add_interaction_to_claim(
        self,
        claim_id: str,
        interaction_id: str,
        date: str,
        interaction_type: str,
        notes: str,
        participant_id: str
    ) -> dict:
        """
        Records a new interaction for the specified claim.

        Args:
            claim_id (str): The claim's unique identifier.
            interaction_id (str): Unique identifier for the new interaction.
            date (str): ISO date string for the interaction timestamp.
            interaction_type (str): The type/category of the interaction (e.g., note, contact).
            notes (str): Details/content of the interaction.
            participant_id (str): The user or adjuster involved in this interaction.

        Returns:
            dict:
                - On success: {"success": True, "message": "Interaction added to claim <claim_id>"}
                - On failure: {"success": False, "error": "<reason>"}

        Constraints:
            - claim_id must already exist in the system.
            - interaction_id must not already exist.
            - Interactions are timestamped and assigned to claims.
        """
        # Check claim_id exists
        if claim_id not in self.claims:
            return {"success": False, "error": "Claim does not exist"}

        # Check interaction_id uniqueness
        if interaction_id in self.interactions:
            return {"success": False, "error": "Interaction ID already exists"}

        # Build interaction record
        interaction = {
            "interaction_id": interaction_id,
            "claim_id": claim_id,
            "date": date,
            "interaction_type": interaction_type,
            "notes": notes,
            "participant_id": participant_id
        }

        # Store the interaction
        self.interactions[interaction_id] = interaction

        # Add interaction_id to the claim's interactions list
        if "interactions" not in self.claims[claim_id] or self.claims[claim_id]["interactions"] is None:
            self.claims[claim_id]["interactions"] = []
        self.claims[claim_id]["interactions"].append(interaction_id)

        return {"success": True, "message": f"Interaction added to claim {claim_id}"}

    def delete_claim(self, claim_id: str, user_id: str) -> dict:
        """
        Remove an existing claim and all its associated documents and interactions.
        (Admin-level action only.)

        Args:
            claim_id (str): The unique identifier of the claim to delete.
            user_id (str): The user requesting the operation (must be admin).

        Returns:
            dict: {
                "success": True,
                "message": "Claim <claim_id> deleted."
            }
            or
            {
                "success": False,
                "error": "<description of error>"
            }

        Constraints:
            - Only admin users may delete claims.
            - All supporting documents and interactions linked to the claim are also deleted.
            - claim_id must exist.
        """

        # Placeholder admin check.
        def is_admin(user_id: str) -> bool:
            # In a real system, check user roles. Here, assume user_id == "admin" or hardcode.
            # For demonstration, only "admin" is considered admin.
            return user_id == "admin"

        if not is_admin(user_id):
            return {"success": False, "error": "Permission denied: Only admin users may delete claims."}

        if claim_id not in self.claims:
            return {"success": False, "error": f"Claim ID {claim_id} does not exist."}

        # Remove associated documents
        docs_to_delete = [doc_id for doc_id, doc_info in self.documents.items() if doc_info["claim_id"] == claim_id]
        for doc_id in docs_to_delete:
            del self.documents[doc_id]

        # Remove associated interactions
        interactions_to_delete = [int_id for int_id, int_info in self.interactions.items() if int_info["claim_id"] == claim_id]
        for int_id in interactions_to_delete:
            del self.interactions[int_id]

        # Remove the claim itself
        del self.claims[claim_id]

        return {"success": True, "message": f"Claim {claim_id} deleted."}

    def update_payout_amount(self, claim_id: str, payout_amount: float) -> dict:
        """
        Set or change the payout amount for a resolved claim.
    
        Args:
            claim_id (str): The claim to update.
            payout_amount (float): The payout amount to set. Must be non-negative.
        
        Returns:
            dict: {
                "success": True,
                "message": "Payout amount updated for claim <claim_id>"
            }
            or
            {
                "success": False,
                "error": <reason>
            }
        
        Constraints:
            - claim_id must exist.
            - payout_amount must be non-negative.
            - Claim must be in a resolved status ("Approved", "Denied", "Paid Out").
        """
        allowed_statuses = {"Approved", "Denied", "Paid Out"}

        if claim_id not in self.claims:
            return { "success": False, "error": "Claim does not exist" }
        if not isinstance(payout_amount, (int, float)) or payout_amount < 0:
            return { "success": False, "error": "Invalid payout amount; must be non-negative number" }
        claim = self.claims[claim_id]
        if claim["status"] not in allowed_statuses:
            return { "success": False, "error": f"Claim status '{claim['status']}' does not permit payout update" }

        claim["payout_amount"] = payout_amount
        self.claims[claim_id] = claim  # Not strictly necessary for dictionaries, but keeping for clarity

        return {
            "success": True,
            "message": f"Payout amount updated for claim {claim_id}"
        }

    def set_claim_resolution_date(self, claim_id: str, resolution_date: str) -> dict:
        """
        Assign or modify the resolution date for a claim.

        Args:
            claim_id (str): The unique identifier for the claim.
            resolution_date (str): ISO date string to set as the claim's resolution date (format: YYYY-MM-DD).

        Returns:
            dict: 
                - On success: {"success": True, "message": "Claim resolution date updated successfully." }
                - On failure: {"success": False, "error": "reason" }

        Constraints:
            - claim_id must exist in the system.
            - resolution_date should be a valid ISO date string ("YYYY-MM-DD"). Minimal format check only.
            - Authorization checks are not performed due to lack of user context.
        """
        # Check if claim exists
        if claim_id not in self.claims:
            return {"success": False, "error": "Claim does not exist."}

        # Minimal validation of ISO date string (does not check full date validity, just format)
        if not isinstance(resolution_date, str) or len(resolution_date) != 10 or resolution_date[4] != '-' or resolution_date[7] != '-':
            return {"success": False, "error": "Invalid resolution date format. Must be ISO 'YYYY-MM-DD'."}

        # Update the claim's resolution_date
        self.claims[claim_id]["resolution_date"] = resolution_date

        return {"success": True, "message": "Claim resolution date updated successfully."}


class InsuranceClaimsManagementSystem(BaseEnv):
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

    def get_claim_by_id(self, **kwargs):
        return self._call_inner_tool('get_claim_by_id', kwargs)

    def get_claim_status(self, **kwargs):
        return self._call_inner_tool('get_claim_status', kwargs)

    def list_claims_by_policyholder(self, **kwargs):
        return self._call_inner_tool('list_claims_by_policyholder', kwargs)

    def get_policyholder_by_id(self, **kwargs):
        return self._call_inner_tool('get_policyholder_by_id', kwargs)

    def get_documents_for_claim(self, **kwargs):
        return self._call_inner_tool('get_documents_for_claim', kwargs)

    def get_document_by_id(self, **kwargs):
        return self._call_inner_tool('get_document_by_id', kwargs)

    def get_interactions_for_claim(self, **kwargs):
        return self._call_inner_tool('get_interactions_for_claim', kwargs)

    def get_interaction_by_id(self, **kwargs):
        return self._call_inner_tool('get_interaction_by_id', kwargs)

    def get_adjuster_by_id(self, **kwargs):
        return self._call_inner_tool('get_adjuster_by_id', kwargs)

    def get_claims_by_status(self, **kwargs):
        return self._call_inner_tool('get_claims_by_status', kwargs)

    def check_user_authorization_for_claim(self, **kwargs):
        return self._call_inner_tool('check_user_authorization_for_claim', kwargs)

    def get_claim_history(self, **kwargs):
        return self._call_inner_tool('get_claim_history', kwargs)

    def submit_new_claim(self, **kwargs):
        return self._call_inner_tool('submit_new_claim', kwargs)

    def update_claim_status(self, **kwargs):
        return self._call_inner_tool('update_claim_status', kwargs)

    def update_claim_info(self, **kwargs):
        return self._call_inner_tool('update_claim_info', kwargs)

    def assign_adjuster_to_claim(self, **kwargs):
        return self._call_inner_tool('assign_adjuster_to_claim', kwargs)

    def add_supporting_document_to_claim(self, **kwargs):
        return self._call_inner_tool('add_supporting_document_to_claim', kwargs)

    def remove_supporting_document_from_claim(self, **kwargs):
        return self._call_inner_tool('remove_supporting_document_from_claim', kwargs)

    def add_interaction_to_claim(self, **kwargs):
        return self._call_inner_tool('add_interaction_to_claim', kwargs)

    def delete_claim(self, **kwargs):
        return self._call_inner_tool('delete_claim', kwargs)

    def update_payout_amount(self, **kwargs):
        return self._call_inner_tool('update_payout_amount', kwargs)

    def set_claim_resolution_date(self, **kwargs):
        return self._call_inner_tool('set_claim_resolution_date', kwargs)
