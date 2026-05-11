# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Any
import uuid
from datetime import datetime



# Represents employees or service providers submitting claims
class UserInfo(TypedDict):
    _id: str
    name: str
    role: str
    department: str
    contact_info: str

# Represents a reimbursement claim
class ClaimInfo(TypedDict):
    claim_id: str
    user_id: str
    amount: float
    date_submitted: str
    status: str
    category: str
    payment_sta: str  # Assumed typo for payment_status

# Represents supporting documentation for a claim
class DocumentInfo(TypedDict):
    document_id: str
    claim_id: str
    file_type: str
    file_location: str
    upload_da: str  # Assumed typo for upload_date

# Represents approval workflow for a claim
class ApprovalWorkflowInfo(TypedDict):
    claim_id: str
    current_step: str
    approver_id: str
    approval_history: List[Any]  # Could refine type if format known

class _GeneratedEnvImpl:
    def __init__(self):
        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}
        # Claims: {claim_id: ClaimInfo}
        self.claims: Dict[str, ClaimInfo] = {}
        # Documents: {document_id: DocumentInfo}
        self.documents: Dict[str, DocumentInfo] = {}
        # Approval Workflows: {claim_id: ApprovalWorkflowInfo}
        self.approval_workflows: Dict[str, ApprovalWorkflowInfo] = {}
        
        # Constraints:
        # - Each claim must be associated with a user.
        # - Each claim must have at least one status (e.g., submitted, under review, approved, paid, rejected).
        # - Supporting documentation should be associated with the correct claim.
        # - Only authorized users can change claim status or access claim details.
        # - Claims can only progress through workflow steps in valid sequences.

    def _get_workflow(self, claim_id: str):
        workflow = self.approval_workflows.get(claim_id)
        if workflow is not None:
            return workflow

        # Some formal cases store workflows under arbitrary ids like
        # AW-550 / aw_001 while the workflow payload itself still points
        # at the real claim_id. Normalize that access pattern on demand.
        for key, candidate in list(self.approval_workflows.items()):
            if isinstance(candidate, dict) and candidate.get("claim_id") == claim_id:
                self.approval_workflows[claim_id] = candidate
                if key != claim_id:
                    del self.approval_workflows[key]
                return candidate

        return None

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user information by user _id.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo  # User's information as a dictionary.
            }
            or
            {
                "success": False,
                "error": str  # Error message if user not found or invalid input.
            }

        Constraints:
            - The user with the specified _id must exist.
        """
        if not isinstance(user_id, str) or not user_id:
            return { "success": False, "error": "Invalid user_id provided" }
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user }

    def get_user_by_name(self, name: str) -> dict:
        """
        Retrieve information for all users with the specified name.

        Args:
            name (str): The name to search for (exact match).

        Returns:
            dict: {
                "success": True,
                "data": List[UserInfo]  # List of user info dicts, possibly empty
            }

        Constraints:
            - Multiple users with the same name may exist.
            - Empty result list is valid if no user matches.
            - No error or authorization handling for querying by name.
        """
        matches = [
            user_info for user_info in self.users.values()
            if user_info["name"] == name
        ]
        return { "success": True, "data": matches }

    def list_all_users(self) -> dict:
        """
        Retrieve a list of all users registered in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[UserInfo]  # All user info objects. May be empty if no users.
            }
        Constraints:
            - No authorization is required for this query.
            - No error is raised if there are no users; data=[] in that case.
        """
        user_list = list(self.users.values())
        return { "success": True, "data": user_list }

    def get_claim_by_id(self, claim_id: str) -> dict:
        """
        Retrieve detailed information for a claim by claim_id.

        Args:
            claim_id (str): The unique identifier of the claim.

        Returns:
            dict:
                - On success:
                    {"success": True, "data": ClaimInfo }
                - On failure:
                    {"success": False, "error": "Claim not found" }

        Constraints:
            - The claim_id must exist in the claims database.
        """
        claim = self.claims.get(claim_id)
        if claim is None:
            return {"success": False, "error": "Claim not found"}
        return {"success": True, "data": claim}

    def get_claim_status(self, claim_id: str) -> dict:
        """
        Retrieve the current status of a claim by its claim_id.

        Args:
            claim_id (str): The unique identifier of the claim.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "claim_id": str,
                    "status": str
                }
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (e.g., claim not found)
            }

        Constraints:
            - The claim must exist in the system.
        """
        claim = self.claims.get(claim_id)
        if not claim:
            return { "success": False, "error": "Claim not found" }

        return {
            "success": True,
            "data": {
                "claim_id": claim_id,
                "status": claim["status"]
            }
        }

    def list_claims_by_user(self, user_id: str) -> dict:
        """
        List all claims submitted by a specific user.

        Args:
            user_id (str): The unique ID ('_id') of the user whose claims are to be listed.

        Returns:
            dict: {
                "success": True,
                "data": List[ClaimInfo],  # All claims submitted by this user (may be empty).
            }
            or
            {
                "success": False,
                "error": str  # E.g. "User does not exist"
            }

        Constraints:
            - The user must exist in the system.
            - Returns all claims where claim['user_id'] == user_id.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        result = [
            claim for claim in self.claims.values()
            if claim["user_id"] == user_id
        ]

        return {"success": True, "data": result}

    def list_claims_by_status(self, status: str) -> dict:
        """
        Retrieve all claims whose status matches the given status string.

        Args:
            status (str): The claim status to filter for (e.g., "approved", "submitted").

        Returns:
            dict: {
                "success": True,
                "data": List[ClaimInfo],  # List of claims with matching status (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Description if input is missing or invalid
            }

        Constraints:
            - Returns all claims whose 'status' equals the given value. 
            - Returns an empty list if no claims match.
            - Fails only if the given status is not a string or is missing.
        """
        if not isinstance(status, str) or status.strip() == "":
            return {"success": False, "error": "Invalid or missing status parameter"}

        matching_claims = [
            claim_info
            for claim_info in self.claims.values()
            if claim_info.get("status") == status
        ]
        return {"success": True, "data": matching_claims}

    def get_claim_documents(self, claim_id: str) -> dict:
        """
        List all supporting documents attached to a given claim.

        Args:
            claim_id (str): The unique identifier for the claim.

        Returns:
            dict: 
                - On success: {
                     "success": True,
                     "data": List[DocumentInfo]  # List may be empty if no documents attached
                  }
                - On failure (claim not found): {
                     "success": False,
                     "error": "Claim does not exist"
                  }

        Constraints:
            - The specified claim must exist.
            - Only documents with a matching claim_id are included.
        """
        if claim_id not in self.claims:
            return { "success": False, "error": "Claim does not exist" }
    
        docs = [
            doc_info for doc_info in self.documents.values()
            if doc_info["claim_id"] == claim_id
        ]

        return { "success": True, "data": docs }

    def get_document_by_id(self, document_id: str) -> dict:
        """
        Retrieve information for a specific document by its document_id.

        Args:
            document_id (str): The ID of the document to retrieve.

        Returns:
            dict:
                - On success: {
                    "success": True,
                    "data": DocumentInfo
                  }
                - On failure (not found): {
                    "success": False,
                    "error": "Document not found"
                  }

        Constraints:
            - The document_id must exist in the system for a successful return.
        """
        doc = self.documents.get(document_id)
        if doc is not None:
            return {"success": True, "data": doc}
        else:
            return {"success": False, "error": "Document not found"}

    def get_approval_workflow_by_claim(self, claim_id: str) -> dict:
        """
        Retrieve the approval workflow (current step, approver, history) for a given claim.

        Args:
            claim_id (str): The claim's unique identifier.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": ApprovalWorkflowInfo  # The approval workflow info for the claim
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason for the failure
                    }
        Constraints:
            - claim_id must correspond to an existing claim.
            - There must be an approval workflow associated with the claim.
        """
        if claim_id not in self.claims:
            return {"success": False, "error": "Claim does not exist"}
        workflow = self._get_workflow(claim_id)
        if not workflow:
            return {"success": False, "error": "No approval workflow found for this claim"}
        return {"success": True, "data": workflow}

    def list_all_claims(self) -> dict:
        """
        Retrieve all claims present in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[ClaimInfo],  # List of all claims (can be empty)
            }
        """
        all_claims = list(self.claims.values())
        return {
            "success": True,
            "data": all_claims
        }

    def get_claims_by_category(self, category: str) -> dict:
        """
        Retrieve all claims filtered by the provided category.
    
        Args:
            category (str): The claim category to filter by (e.g., "travel", "meals").
    
        Returns:
            dict: {
                "success": True,
                "data": List[ClaimInfo],  # All claims where claim['category'] matches the given category
            } 
            or 
            {
                "success": False,
                "error": str  # If input is invalid
            }
    
        Constraints:
            - category must be a non-empty string.
            - Matching is case-insensitive for user friendliness.
        """
        if not category or not isinstance(category, str):
            return { "success": False, "error": "Category parameter is required." }

        result = [
            claim for claim in self.claims.values()
            if claim.get("category", "").lower() == category.lower()
        ]
        return { "success": True, "data": result }

    def get_claim_payment_status(self, claim_id: str) -> dict:
        """
        Retrieve the payment status for a given claim.

        Args:
            claim_id (str): The unique identifier for the claim.

        Returns:
            dict:
                - If found: { "success": True, "data": <payment_status (str)> }
                - If not found: { "success": False, "error": "Claim not found" }
                - If claim found but missing payment status: { "success": False, "error": "Payment status not available for this claim" }
        """
        claim = self.claims.get(claim_id)
        if claim is None:
            return { "success": False, "error": "Claim not found" }
        payment_status = claim.get("payment_sta")
        if payment_status is None:
            return { "success": False, "error": "Payment status not available for this claim" }
        return { "success": True, "data": payment_status }

    def submit_claim(self, user_id: str, amount: float, category: str, date_submitted: str = None) -> dict:
        """
        Create and submit a new reimbursement claim, associated with a user.

        Args:
            user_id (str): ID of the user submitting the claim. Must exist.
            amount (float): Amount claimed (must be positive).
            category (str): The category/type of the claim.
            date_submitted (str, optional): ISO date string for submission (default: current date).
    
        Returns:
            dict: {
                "success": True,
                "message": "Claim submitted successfully.",
                "claim_id": str  # The new claim's ID
            }
            or
            {
                "success": False,
                "error": str
            }
    
        Constraints:
            - Claim must be associated with an existing user.
            - Status is initialized as "submitted".
            - Payment status is initialized as "unpaid".
        """


        # Validate user existence
        if user_id not in self.users:
            return {"success": False, "error": "User not found."}

        # Validate amount
        if not isinstance(amount, (int, float)) or amount <= 0:
            return {"success": False, "error": "Amount must be a positive number."}

        # Validate category
        if not category or not isinstance(category, str):
            return {"success": False, "error": "Category must be a non-empty string."}

        # Prepare claim_id and date_submitted
        claim_id = str(uuid.uuid4())
        if not date_submitted:
            date_submitted = datetime.utcnow().isoformat()

        claim_data = {
            "claim_id": claim_id,
            "user_id": user_id,
            "amount": float(amount),
            "date_submitted": date_submitted,
            "status": "submitted",
            "category": category,
            "payment_sta": "unpaid"
        }

        self.claims[claim_id] = claim_data

        # Optionally, initialize approval workflow for this claim
        if claim_id not in self.approval_workflows:
            self.approval_workflows[claim_id] = {
                "claim_id": claim_id,
                "current_step": "submitted",
                "approver_id": "",
                "approval_history": []
            }

        return {
            "success": True,
            "message": "Claim submitted successfully.",
            "claim_id": claim_id
        }

    def update_claim_status(self, claim_id: str, new_status: str, user_id: str) -> dict:
        """
        Change the status of a claim (e.g., to approved, paid, rejected),
        only if the user is authorized and the transition is allowed by workflow rules.

        Args:
            claim_id (str): The claim to update.
            new_status (str): The new status to set (e.g., approved, paid, rejected).
            user_id (str): The user attempting the status change.

        Returns:
            dict: 
                On success:
                    {"success": True, "message": "Claim status updated to <new_status>"}
                On failure:
                    {"success": False, "error": "<reason>"}

        Constraints:
            - Claim must exist.
            - User must exist and be authorized (current approver, 'manager', or 'admin').
            - Only allowed transitions by workflow.
        """
        # 1. Validate claim
        claim = self.claims.get(claim_id)
        if not claim:
            return {"success": False, "error": "Claim does not exist"}

        # 2. Validate user
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User does not exist"}

        # 3. Check if workflow exists
        workflow = self._get_workflow(claim_id)
        if not workflow:
            return {"success": False, "error": "Approval workflow not found for claim"}

        # 4. Authorization check: 
        #    - user is the current approver,
        #    OR user.role is 'manager' or 'admin'
        authorized_roles = {'manager', 'admin'}
        if user['role'] not in authorized_roles and user_id != workflow['approver_id']:
            return {"success": False, "error": "User not authorized to change claim status"}

        # 5. Workflow state transition validity
        #    Define allowed transitions.
        allowed_transitions = {
            "submitted": ["under review", "rejected"],
            "under review": ["approved", "rejected"],
            "approved": ["paid"],
            "paid": [],
            "rejected": []
        }
        current_status = claim['status']
        if new_status == current_status:
            return {"success": False, "error": "Claim is already in the requested status"}

        valid_next_statuses = allowed_transitions.get(current_status, [])
        review_steps_allowing_final_approval = {
            "initial_review",
            "manager_review",
            "compliance_check",
            "finance_review",
            "admin_review",
            "director_review",
            "manager_approval",
        }
        can_direct_approve = (
            current_status == "submitted"
            and new_status == "approved"
            and workflow.get("approver_id") == user_id
            and workflow.get("current_step") in review_steps_allowing_final_approval
        )
        if new_status not in valid_next_statuses and not can_direct_approve:
            return {"success": False, "error": f"Invalid status transition from {current_status} to {new_status}"}

        # 6. Update the claim's status
        claim['status'] = new_status

        # 7. Optionally, update workflow's history (if present)
        if 'approval_history' in workflow and isinstance(workflow['approval_history'], list):
            workflow['approval_history'].append({
                "user_id": user_id,
                "old_status": current_status,
                "new_status": new_status
            })
        workflow['current_step'] = new_status

        return {"success": True, "message": f"Claim status updated to {new_status}"}

    def attach_document_to_claim(
        self,
        claim_id: str,
        document_id: str,
        file_type: str,
        file_location: str,
        upload_date: str
    ) -> dict:
        """
        Upload and associate a new supporting document with a claim.

        Args:
            claim_id (str): The ID of the claim to attach the document to.
            document_id (str): Unique identifier for the new document.
            file_type (str): The document's file type (e.g., 'pdf', 'jpg').
            file_location (str): The file storage location or path.
            upload_date (str): The upload date (ISO date string recommended).

        Returns:
            dict: {
                "success": True,
                "message": "Document attached to claim."
            }
            or
            {
                "success": False,
                "error": <error_message>
            }

        Constraints:
            - claim_id must exist in the claim registry.
            - document_id must be unique (not already used).
            - Document will be associated (via claim_id) to the correct claim.
        """
        if claim_id not in self.claims:
            return {"success": False, "error": "Claim does not exist."}
        if document_id in self.documents:
            return {"success": False, "error": "Document ID already exists."}
        if not all([claim_id, document_id, file_type, file_location, upload_date]):
            return {"success": False, "error": "Missing required document fields."}
        # Create and add document record
        doc_info = {
            "document_id": document_id,
            "claim_id": claim_id,
            "file_type": file_type,
            "file_location": file_location,
            "upload_da": upload_date,  # 'upload_da' as in provided TypedDict
        }
        self.documents[document_id] = doc_info
        return {
            "success": True,
            "message": f"Document {document_id} attached to claim {claim_id}."
        }

    def advance_approval_workflow(self, claim_id: str) -> dict:
        """
        Advance the approval workflow for a claim to the next step in the predefined sequence.

        Args:
            claim_id (str): The unique claim identifier whose workflow to advance.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Approval workflow for claim <claim_id> advanced from <old_step> to <new_step>"
                    }
                On failure:
                    {
                        "success": False,
                        "error": <reason>
                    }

        Constraints:
            - The claim and approval workflow must exist.
            - Workflow can only move to the next defined step.
            - Cannot advance workflow if at the final step.
        """
        # Define supported workflow progressions based on the formal case states
        # used throughout this environment.
        NEXT_STEP_BY_CURRENT = {
            "submitted": "under review",
            "under review": "approved",
            "approved": "paid",
            "initial_review": "manager_review",
            "manager_review": "compliance_check",
            "compliance_check": "approved",
            "finance_review": "approved",
            "admin_review": "approved",
            "director_review": "approved",
            "manager_approval": "approved",
        }

        # Check whether claim exists
        if claim_id not in self.claims:
            return { "success": False, "error": "Claim does not exist" }

        # Check if workflow for the claim exists
        workflow = self._get_workflow(claim_id)
        if not workflow:
            return { "success": False, "error": "No approval workflow found for claim" }

        current_step = workflow.get("current_step")
        if current_step == "paid":
            return { "success": False, "error": "Workflow already at final step; cannot advance" }
        if current_step not in NEXT_STEP_BY_CURRENT:
            return { "success": False, "error": f"Invalid current step '{current_step}' in workflow" }

        # Compute new step
        new_step = NEXT_STEP_BY_CURRENT[current_step]
        # Update workflow
        workflow["current_step"] = new_step
        # Append to approval history (tracking the transition)
        if isinstance(workflow.get("approval_history"), list):
            workflow["approval_history"].append({
                "from": current_step,
                "to": new_step,
                "action": "advanced"
            })
        else:
            workflow["approval_history"] = [{
                "from": current_step,
                "to": new_step,
                "action": "advanced"
            }]

        return {
            "success": True,
            "message": f"Approval workflow for claim {claim_id} advanced from {current_step} to {new_step}"
        }

    def assign_approver_to_claim(self, claim_id: str, approver_id: str, requestor_id: str) -> dict:
        """
        Set or reset the approver for the specified claim's current approval workflow step.

        Args:
            claim_id (str): The claim to modify.
            approver_id (str): The user ID of the new approver.
            requestor_id (str): The user ID performing the operation (for authorization).

        Returns:
            dict: 
                On success:
                    { "success": True, "message": "Approver assigned to claim <claim_id>." }
                On failure:
                    { "success": False, "error": "<reason>" }

        Constraints:
            - Claim must exist.
            - ApprovalWorkflow for the claim must exist.
            - Approver user must exist.
            - Only authorized users (role == 'admin' or 'manager') may assign approvers.
        """
        # Check requestor authorization
        requestor = self.users.get(requestor_id)
        if not requestor:
            return {"success": False, "error": "Requestor user does not exist."}
        if requestor["role"] not in ("admin", "manager"):
            return {"success": False, "error": "Permission denied: not authorized to assign approver."}

        # Check claim existence
        claim = self.claims.get(claim_id)
        if not claim:
            return {"success": False, "error": "Claim does not exist."}

        # Check workflow existence
        workflow = self._get_workflow(claim_id)
        if not workflow:
            return {"success": False, "error": "Approval workflow for claim does not exist."}

        # Check approver existence
        approver = self.users.get(approver_id)
        if not approver:
            return {"success": False, "error": "Specified approver user does not exist."}

        # Assign approver, with history recording
        previous_approver = workflow.get("approver_id")
        workflow["approver_id"] = approver_id
        if "approval_history" in workflow and isinstance(workflow["approval_history"], list):
            workflow["approval_history"].append({
                "action": "assigned_approver",
                "from": previous_approver,
                "to": approver_id,
                "by": requestor_id
            })

        return {"success": True, "message": f"Approver assigned to claim {claim_id}."}

    def reject_claim(self, claim_id: str, user_id: str) -> dict:
        """
        Change the status of a claim to "rejected" and log this action in the workflow.

        Args:
            claim_id (str): The unique identifier of the claim to reject.
            user_id (str): ID of the user attempting the rejection; must be authorized.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Claim <claim_id> rejected and workflow updated." }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - Only authorized users may reject claims (role is typically 'manager', 'admin', or similar).
            - Claim must exist.
            - Claim must not already be 'rejected' or 'paid'.
            - Approval workflow must exist for the claim.
            - Status/state sequence must be valid.
        """

        # Ensure claim exists
        claim = self.claims.get(claim_id)
        if not claim:
            return {"success": False, "error": "Claim does not exist."}
    
        # Ensure user exists and is authorized
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User does not exist."}
        if user["role"].lower() not in ["admin", "manager", "approver"]:
            return {"success": False, "error": "User not authorized to reject claims."}
    
        # Validate claim status
        if claim["status"].lower() in ["rejected", "paid"]:
            return {"success": False, "error": f"Claim is already {claim['status']}."}

        # Ensure workflow exists
        workflow = self._get_workflow(claim_id)
        if not workflow:
            return {"success": False, "error": "Approval workflow not found for this claim."}
    
        # Valid state transition: (can add to this list to restrict further)
        # We'll reject from any non-terminal state except already rejected/paid
        old_status = claim["status"]

        # Update claim status
        claim["status"] = "rejected"
        self.claims[claim_id] = claim

        # Update workflow
        workflow["current_step"] = "rejected"
        if "approval_history" not in workflow or not isinstance(workflow["approval_history"], list):
            workflow["approval_history"] = []
        workflow["approval_history"].append({
            "action": "rejected",
            "by": user_id,
            "old_status": old_status,
            "new_status": "rejected"
        })
        self.approval_workflows[claim_id] = workflow

        return {
            "success": True,
            "message": f"Claim {claim_id} rejected and workflow updated."
        }

    def mark_claim_as_paid(self, claim_id: str) -> dict:
        """
        Update a claim's status and payment status to 'paid' after reimbursement.

        Args:
            claim_id (str): The unique identifier for the claim to update.

        Returns:
            dict: 
              - {"success": True, "message": "Claim marked as paid."}
              - {"success": False, "error": "reason"}

        Constraints:
            - Claim must exist.
            - Claim's status must allow transition to "paid" (commonly: status == "approved").
            - If claim is already "paid", return an error.
            - (Authorization should be handled externally, or only privileged users may call.)
        """
        claim = self.claims.get(claim_id)
        if not claim:
            return {"success": False, "error": "Claim does not exist."}

        # Avoid transition if already paid
        if claim.get("status", "").lower() == "paid" or claim.get("payment_sta", "").lower() == "paid":
            return {"success": False, "error": "Claim is already marked as paid."}

        # Typically, only "approved" claims can be marked as paid
        # Consider synonyms for status, e.g., status might contain "approved"
        status = claim.get("status", "").lower()
        if status not in ["approved", "under payment", "ready for payment"]:  # common intermediate states
            return {"success": False, "error": f"Claim status '{claim.get('status', '')}' does not allow marking as paid."}

        # Update status and payment status
        claim["status"] = "paid"
        claim["payment_sta"] = "paid"

        # Save back to the claims dict (redundant for dict-in-place, but explicit)
        self.claims[claim_id] = claim

        return {"success": True, "message": "Claim marked as paid."}

    def delete_claim(self, claim_id: str, user_id: str) -> dict:
        """
        Remove a claim from the system (admin or allowed user action).

        Args:
            claim_id (str): The unique ID of the claim to delete.
            user_id (str): The ID of the user attempting to delete the claim.

        Returns:
            dict: {
                "success": True,
                "message": "Claim deleted."
            } or {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - Claim must exist.
            - Only admin or the claim owner can delete a claim.
            - Associated documents and approval workflow must also be removed.
        """
        claim = self.claims.get(claim_id)
        if not claim:
            return {"success": False, "error": "Claim does not exist."}

        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User does not exist."}

        is_admin = user.get("role", "").lower() == "admin"
        is_claim_owner = claim["user_id"] == user_id

        # Only admin or claim owner can delete
        if not (is_admin or is_claim_owner):
            return {"success": False, "error": "Permission denied: not allowed to delete this claim."}

        # Remove documents associated with the claim
        to_remove_doc_ids = [
            doc_id for doc_id, doc in self.documents.items()
            if doc.get("claim_id") == claim_id
        ]
        for doc_id in to_remove_doc_ids:
            del self.documents[doc_id]
    
        # Remove approval workflow associated with the claim
        if claim_id in self.approval_workflows:
            del self.approval_workflows[claim_id]
    
        # Remove the claim
        del self.claims[claim_id]

        return {"success": True, "message": "Claim deleted."}

    def remove_document_from_claim(self, document_id: str) -> dict:
        """
        Detach or delete a document associated with a claim.

        Args:
            document_id (str): The unique identifier of the document to be removed.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "message": "Document detached/deleted from claim."
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Error description.
                    }

        Constraints:
            - The specified document_id must exist in the system.
            - The document must be associated with a claim (document.claim_id should refer to an existing claim).
            - Document will be deleted from application's internal data storage.
        """
        if document_id not in self.documents:
            return {
                "success": False,
                "error": "Document does not exist."
            }

        document_info = self.documents[document_id]
        claim_id = document_info.get("claim_id")

        # Optional integrity check: Claim should exist, but even if not, we remove the document
        if not claim_id or claim_id not in self.claims:
            # Still proceed with deletion, but notify about lack of valid claim
            del self.documents[document_id]
            return {
                "success": True,
                "message": "Document deleted, but its associated claim does not exist."
            }

        # If all is well, just remove the document from records
        del self.documents[document_id]
        return {
            "success": True,
            "message": "Document detached/deleted from claim."
        }

    def update_claim_amount(self, claim_id: str, new_amount: float, acting_user_id: str) -> dict:
        """
        Modify the amount of a claim, only if it is in an editable state and the user is authorized.

        Args:
            claim_id (str): ID of the claim to update.
            new_amount (float): The new amount to set (must be positive).
            acting_user_id (str): The user who is attempting the modification.

        Returns:
            dict: {
                "success": True,
                "message": "Claim amount updated successfully."
            }
            OR
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The claim must exist.
            - Only claim owner or admins can modify.
            - Claim status must be 'submitted' or 'under review'.
            - new_amount must be positive.
        """

        # Validate claim existence
        claim = self.claims.get(claim_id)
        if not claim:
            return { "success": False, "error": "Claim not found." }

        # Validate user existence
        acting_user = self.users.get(acting_user_id)
        if not acting_user:
            return { "success": False, "error": "User not found." }

        # Check user authorization (owner or admin/finance)
        is_owner = (claim["user_id"] == acting_user_id)
        is_admin = acting_user["role"].lower() in ["admin", "finance"]
        if not (is_owner or is_admin):
            return { "success": False, "error": "Permission denied. User not authorized to update claim amount." }

        # Validate claim status
        editable_statuses = ["submitted", "under review"]
        if claim["status"].lower() not in editable_statuses:
            return { "success": False, "error": f"Claim cannot be edited in current status: {claim['status']}." }

        # Validate amount
        if not isinstance(new_amount, (float, int)) or new_amount <= 0:
            return { "success": False, "error": "Amount must be a positive number." }

        # Update the claim amount
        claim["amount"] = float(new_amount)
        # Optionally, update date_submitted or keep audit trail elsewhere

        return { "success": True, "message": "Claim amount updated successfully." }

    def edit_claim_details(
        self,
        claim_id: str,
        user_id: str,
        details_to_update: dict
    ) -> dict:
        """
        Change editable details (category, date_submitted, amount, etc.) of a claim
        before certain workflow stages (typically when status is 'submitted').

        Args:
            claim_id (str): The ID of the claim to edit.
            user_id (str): The ID of the user attempting the edit.
            details_to_update (dict): Dictionary of fields to update and their new values.

        Returns:
            dict:
                {
                    "success": True,
                    "message": "Claim details updated successfully."
                }
                or
                {
                    "success": False,
                    "error": "reason for failure"
                }

        Constraints:
            - Claim must exist.
            - Claim may only be edited if status is 'submitted'.
            - Only the user who created the claim may edit it (user_id == claim.user_id).
            - Only editable fields may be changed (category, date_submitted, amount).
            - Other fields (claim_id, user_id, status, payment_sta, etc.) cannot be edited here.
        """
        editable_fields = {"category", "date_submitted", "amount"}

        # 1. Validate claim exists
        claim = self.claims.get(claim_id)
        if claim is None:
            return {"success": False, "error": "Claim does not exist."}

        # 2. Verify user is owner of claim
        if claim["user_id"] != user_id:
            return {"success": False, "error": "User not authorized to edit this claim."}

        # 3. Check allowed workflow stage (only if status is 'submitted')
        if claim["status"].lower() != "submitted":
            return {"success": False, "error": "Claim cannot be edited at its current workflow stage."}

        # 4. Check if trying to edit non-editable fields
        for field in details_to_update:
            if field not in editable_fields:
                return {"success": False, "error": f"Field '{field}' cannot be edited."}

        # 5. Update the claim
        for field, new_value in details_to_update.items():
            claim[field] = new_value

        self.claims[claim_id] = claim

        return {"success": True, "message": "Claim details updated successfully."}


class ExpenseReimbursementManagementSystem(BaseEnv):
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
            if key == "approval_workflows" and isinstance(value, dict):
                normalized = {}
                for wf_key, wf_value in value.items():
                    wf_copy = copy.deepcopy(wf_value)
                    if isinstance(wf_copy, dict):
                        claim_id = wf_copy.get("claim_id")
                        if isinstance(claim_id, str) and claim_id:
                            normalized[claim_id] = wf_copy
                            continue
                    normalized[wf_key] = wf_copy
                setattr(env, key, normalized)
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

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def get_user_by_name(self, **kwargs):
        return self._call_inner_tool('get_user_by_name', kwargs)

    def list_all_users(self, **kwargs):
        return self._call_inner_tool('list_all_users', kwargs)

    def get_claim_by_id(self, **kwargs):
        return self._call_inner_tool('get_claim_by_id', kwargs)

    def get_claim_status(self, **kwargs):
        return self._call_inner_tool('get_claim_status', kwargs)

    def list_claims_by_user(self, **kwargs):
        return self._call_inner_tool('list_claims_by_user', kwargs)

    def list_claims_by_status(self, **kwargs):
        return self._call_inner_tool('list_claims_by_status', kwargs)

    def get_claim_documents(self, **kwargs):
        return self._call_inner_tool('get_claim_documents', kwargs)

    def get_document_by_id(self, **kwargs):
        return self._call_inner_tool('get_document_by_id', kwargs)

    def get_approval_workflow_by_claim(self, **kwargs):
        return self._call_inner_tool('get_approval_workflow_by_claim', kwargs)

    def list_all_claims(self, **kwargs):
        return self._call_inner_tool('list_all_claims', kwargs)

    def get_claims_by_category(self, **kwargs):
        return self._call_inner_tool('get_claims_by_category', kwargs)

    def get_claim_payment_status(self, **kwargs):
        return self._call_inner_tool('get_claim_payment_status', kwargs)

    def submit_claim(self, **kwargs):
        return self._call_inner_tool('submit_claim', kwargs)

    def update_claim_status(self, **kwargs):
        return self._call_inner_tool('update_claim_status', kwargs)

    def attach_document_to_claim(self, **kwargs):
        return self._call_inner_tool('attach_document_to_claim', kwargs)

    def advance_approval_workflow(self, **kwargs):
        return self._call_inner_tool('advance_approval_workflow', kwargs)

    def assign_approver_to_claim(self, **kwargs):
        return self._call_inner_tool('assign_approver_to_claim', kwargs)

    def reject_claim(self, **kwargs):
        return self._call_inner_tool('reject_claim', kwargs)

    def mark_claim_as_paid(self, **kwargs):
        return self._call_inner_tool('mark_claim_as_paid', kwargs)

    def delete_claim(self, **kwargs):
        return self._call_inner_tool('delete_claim', kwargs)

    def remove_document_from_claim(self, **kwargs):
        return self._call_inner_tool('remove_document_from_claim', kwargs)

    def update_claim_amount(self, **kwargs):
        return self._call_inner_tool('update_claim_amount', kwargs)

    def edit_claim_details(self, **kwargs):
        return self._call_inner_tool('edit_claim_details', kwargs)
