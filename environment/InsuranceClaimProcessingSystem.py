# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict



class CustomerInfo(TypedDict):
    customer_id: str
    name: str
    contact_information: str
    account_status: str

class ClaimInfo(TypedDict):
    claim_id: str
    customer_id: str
    claim_type: str
    submission_date: str
    status: str
    assigned_reviewer_id: str

class ClaimDocumentInfo(TypedDict):
    document_id: str
    claim_id: str
    document_type: str
    file_name: str
    upload_date: str
    validity_status: str
    reviewer_comment: str

class UserInfo(TypedDict):
    user_id: str
    name: str
    role: str
    permission: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Customers: {customer_id: CustomerInfo}
        # Entity: Customer (customer_id, name, contact_information, account_status)
        self.customers: Dict[str, CustomerInfo] = {}

        # Claims: {claim_id: ClaimInfo}
        # Entity: Claim (claim_id, customer_id, claim_type, submission_date, status, assigned_reviewer_id)
        self.claims: Dict[str, ClaimInfo] = {}

        # Claim Documents: {document_id: ClaimDocumentInfo}
        # Entity: ClaimDocument (document_id, claim_id, document_type, file_name, upload_date, validity_status, reviewer_comment)
        self.claim_documents: Dict[str, ClaimDocumentInfo] = {}

        # Users: {user_id: UserInfo}
        # Entity: User (user_id, name, role, permission)
        self.users: Dict[str, UserInfo] = {}

        # Constraints:
        # - Each Claim must be linked to a valid Customer.
        # - A ClaimDocument must belong to a Claim.
        # - Only authorized Users can validate or change the status of ClaimDocuments.
        # - Each ClaimDocument has an associated document_type and file_name.
        # - Validity of a ClaimDocument must be checked before claims can be approved.

    @staticmethod
    def _has_review_permission(user: UserInfo) -> bool:
        role = str(user.get("role", "")).lower()
        permission = str(user.get("permission", "")).lower()
        return (
            "reviewer" in role
            or "admin" in role
            or "adjuster" in role
            or "review" in permission
            or "validate" in permission
            or "claim_management" in permission
            or "admin" in permission
        )

    @staticmethod
    def _has_comment_permission(user: UserInfo) -> bool:
        permission = str(user.get("permission", "")).lower()
        return _GeneratedEnvImpl._has_review_permission(user) or "write" in permission

    @staticmethod
    def _has_delete_permission(user: UserInfo) -> bool:
        role = str(user.get("role", "")).lower()
        permission = str(user.get("permission", "")).lower()
        return (
            "admin" in role
            or "admin" in permission
            or "delete" in permission
            or "claim_management" in permission
        )

    def get_customer_by_id(self, customer_id: str) -> dict:
        """
        Retrieve information for a specific customer by their customer_id.

        Args:
            customer_id (str): Unique ID of the customer.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": CustomerInfo
                }
                or
                {
                    "success": False,
                    "error": str  # Error message if customer is not found.
                }

        Constraints:
            - Customer with the provided customer_id must exist in the system.
        """
        customer = self.customers.get(customer_id)
        if customer is None:
            return { "success": False, "error": "Customer not found" }
        return { "success": True, "data": customer }

    def list_claims_by_customer(self, customer_id: str) -> dict:
        """
        Retrieve all claims submitted by a specific customer.

        Args:
            customer_id (str): The ID of the customer whose claims are to be listed.

        Returns:
            dict: {
                "success": True,
                "data": List[ClaimInfo]
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (e.g. customer not found)
            }
        Constraints:
            - The provided customer_id must exist in the system.
            - Returns all claims where claim['customer_id'] == customer_id.
            - If the customer has no claims, returns an empty list.
        """
        if customer_id not in self.customers:
            return { "success": False, "error": "Customer not found" }

        claims = [
            claim_info for claim_info in self.claims.values()
            if claim_info["customer_id"] == customer_id
        ]

        return { "success": True, "data": claims }

    def get_claim_by_id(self, claim_id: str) -> dict:
        """
        Retrieve information for a specific claim by its claim_id.

        Args:
            claim_id (str): Unique identifier for the claim.

        Returns:
            dict: {
                "success": True,
                "data": ClaimInfo,  # If claim exists
            }
            or
            {
                "success": False,
                "error": str  # "Claim not found" if the claim_id is invalid/missing
            }

        Constraints:
            - claim_id must exist in the system.
        """
        claim_info = self.claims.get(claim_id)
        if not claim_info:
            return {"success": False, "error": "Claim not found"}
        return {"success": True, "data": claim_info}

    def list_documents_by_claim(self, claim_id: str) -> dict:
        """
        List all documents associated with a particular claim.

        Args:
            claim_id (str): The unique identifier for the claim.

        Returns:
            dict:
                - On success:
                    { "success": True, "data": List[ClaimDocumentInfo] }
                - On failure:
                    { "success": False, "error": str }
        Constraints:
            - The claim with claim_id must exist in the system.
        """
        if claim_id not in self.claims:
            return { "success": False, "error": "Claim does not exist" }

        documents = [
            doc_info for doc_info in self.claim_documents.values()
            if doc_info["claim_id"] == claim_id
        ]
        return { "success": True, "data": documents }

    def get_document_by_type_and_filename(self, claim_id: str, document_type: str, file_name: str) -> dict:
        """
        Retrieve a claim document by document_type and file_name for a specified claim.

        Args:
            claim_id (str): The ID of the claim to which the document belongs.
            document_type (str): The type of document (e.g., 'ID Proof', 'Form').
            file_name (str): The name of the document file.

        Returns:
            dict: {
                "success": True,
                "data": ClaimDocumentInfo
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g. claim or document not found)
            }
        Constraints:
            - The claim with claim_id must exist.
            - The claim document must match all three: claim_id, document_type, file_name.
        """
        # Check that the claim exists
        if claim_id not in self.claims:
            return {"success": False, "error": "Claim does not exist"}

        # Search for the relevant document
        for doc in self.claim_documents.values():
            if (
                doc["claim_id"] == claim_id
                and doc["document_type"] == document_type
                and doc["file_name"] == file_name
            ):
                return {"success": True, "data": doc}

        return {
            "success": False,
            "error": "No matching document found for the given claim, document type, and file name"
        }

    def get_document_by_id(self, document_id: str) -> dict:
        """
        Retrieve full details of a claim document by its document_id.

        Args:
            document_id (str): Unique identifier for the claim document.

        Returns:
            dict: {
                "success": True,
                "data": ClaimDocumentInfo  # Document details if found
            }
            or
            {
                "success": False,
                "error": str  # If document_id does not exist
            }
        """
        doc = self.claim_documents.get(document_id)
        if doc is None:
            return { "success": False, "error": "Claim document not found" }
        return { "success": True, "data": doc }

    def check_document_validity_status(self, document_id: str) -> dict:
        """
        Query the current validity status of a specified claim document.

        Args:
            document_id (str): The unique identifier of the claim document.

        Returns:
            dict:
                - If found: { "success": True, "data": str } (validity_status such as 'valid', 'pending', 'invalid', etc.)
                - If not found: { "success": False, "error": "ClaimDocument not found" }

        Constraints:
            - The claim document must exist in the system.
        """
        doc = self.claim_documents.get(document_id)
        if doc is None:
            return { "success": False, "error": "ClaimDocument not found" }

        return { "success": True, "data": doc["validity_status"] }

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve details and permissions for an internal user (reviewer/staff).

        Args:
            user_id (str): The unique ID of the user.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": UserInfo  # User information and permissions
                    }
                - On failure:
                    {
                        "success": False,
                        "error": "User not found"
                    }

        Constraints:
            - The user_id must exist in the users dictionary.
        """
        user = self.users.get(user_id)
        if user is None:
            return {"success": False, "error": "User not found"}
        return {"success": True, "data": user}

    def check_user_permission(self, user_id: str) -> dict:
        """
        Check whether the given user has sufficient permission or role to validate/change
        the status of a ClaimDocument.

        Args:
            user_id (str): The unique ID of the user to check.

        Returns:
            dict:
                - On success: { "success": True, "data": bool }
                  (True if the user has authorization, False otherwise)
                - On error: { "success": False, "error": str }
                  (e.g. user not found)

        Constraints:
            - Only users with specific role(s) or permission(s) are considered authorized
              to validate/change ClaimDocument status.
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }
    
        has_permission = self._has_review_permission(user)

        return { "success": True, "data": has_permission }

    def list_claim_documents_by_status(self, validity_status: str) -> dict:
        """
        List all claim documents that have a specific validity_status.

        Args:
            validity_status (str): The document validity status to filter by ('pending', 'valid', 'invalid', etc).

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[ClaimDocumentInfo],  # Can be empty if no matches.
                    }
                On failure:
                    {
                        "success": False,
                        "error": str,
                    }

        Constraints:
            - validity_status must be provided (non-empty string).
            - No additional constraints apply.
        """
        if not validity_status or not isinstance(validity_status, str):
            return {"success": False, "error": "validity_status must be a non-empty string"}

        filtered_docs = [
            doc for doc in self.claim_documents.values()
            if doc.get("validity_status") == validity_status
        ]

        return {"success": True, "data": filtered_docs}

    def get_claim_status(self, claim_id: str) -> dict:
        """
        Retrieve the current status of a claim by its claim_id.

        Args:
            claim_id (str): The unique identifier for the claim.

        Returns:
            dict:
                If successful:
                    {
                        "success": True,
                        "data": {
                            "claim_id": str,
                            "status": str
                        }
                    }
                If claim not found:
                    {
                        "success": False,
                        "error": "Claim not found"
                    }
        Constraints:
            - The claim_id must exist in the system.
        """
        claim = self.claims.get(claim_id)
        if claim is None:
            return { "success": False, "error": "Claim not found" }

        return {
            "success": True,
            "data": {
                "claim_id": claim_id,
                "status": claim["status"]
            }
        }

    def upload_claim_document(
        self,
        claim_id: str,
        document_type: str,
        file_name: str,
        upload_date: str,
        reviewer_comment: str = ""
    ) -> dict:
        """
        Upload and associate a new document (with document_type, file_name, etc.) to a claim.

        Args:
            claim_id (str): The ID of the claim to which the document will be added.
            document_type (str): The type/category of the document (e.g. 'invoice', 'report').
            file_name (str): The file name of the uploaded document.
            upload_date (str): The upload timestamp (recommended ISO string).
            reviewer_comment (str, optional): Any initial comment; defaults to empty.

        Returns:
            dict: {
                "success": True,
                "message": "Document uploaded and associated with claim."
            }
            or
            {
                "success": False,
                "error": <error_reason>
            }

        Constraints:
            - claim_id must refer to an existing claim.
            - document_type and file_name must be provided (non-empty).
            - Each ClaimDocument must have an associated document_type and file_name.
            - (No explicit check for unique file_name/type for claim unless specified)
        """
        # Check claim existence
        if claim_id not in self.claims:
            return {"success": False, "error": "Claim does not exist"}

        # Validate required fields
        if not document_type or not file_name:
            return {"success": False, "error": "Document type and file name are required"}

        # Generate unique document_id (simple count-based scheme)
        num_docs = len(self.claim_documents)
        new_doc_id = f"DOC-{num_docs + 1}"
        while new_doc_id in self.claim_documents:
            num_docs += 1
            new_doc_id = f"DOC-{num_docs + 1}"

        # Add document: default validity_status to 'pending'
        new_doc_info = {
            "document_id": new_doc_id,
            "claim_id": claim_id,
            "document_type": document_type,
            "file_name": file_name,
            "upload_date": upload_date,
            "validity_status": "pending",
            "reviewer_comment": reviewer_comment
        }
        self.claim_documents[new_doc_id] = new_doc_info

        return {
            "success": True,
            "message": "Document uploaded and associated with claim."
        }

    def validate_claim_document(self, document_id: str, new_status: str, user_id: str) -> dict:
        """
        Update the validity_status of a claim document.
    
        Args:
            document_id (str): The ID of the document to validate.
            new_status (str): The new validity status (e.g., "valid", "invalid", "pending").
            user_id (str): The user performing the validation.
    
        Returns:
            dict: {
                "success": True,
                "message": "Document validity status updated successfully."
            }
            or
            {
                "success": False,
                "error": "<error description>"
            }
    
        Constraints:
            - Only authorized users may perform this operation (user has permission).
            - Claim document must exist.
            - Status must be an allowed value ("valid", "invalid", "pending").
        """
        allowed_statuses = {"valid", "invalid", "pending"}
        if document_id not in self.claim_documents:
            return {"success": False, "error": "Claim document not found."}
        if user_id not in self.users:
            return {"success": False, "error": "User not found."}
        if new_status not in allowed_statuses:
            return {"success": False, "error": "Invalid validity status provided."}

        user = self.users[user_id]
        is_authorized = self._has_review_permission(user)
        if not is_authorized:
            return {"success": False, "error": "User not authorized to validate claim documents."}

        self.claim_documents[document_id]["validity_status"] = new_status
        return {"success": True, "message": "Document validity status updated successfully."}

    def add_reviewer_comment_to_document(self, user_id: str, document_id: str, comment: str) -> dict:
        """
        Attach or update a reviewer comment on a claim document.
    
        Args:
            user_id (str): The internal staff/reviewer making the comment.
            document_id (str): The claim document being commented on.
            comment (str): The comment to attach or update.
    
        Returns:
            dict: 
                On success:
                    {"success": True, "message": "Reviewer comment updated on document <document_id>."}
                On failure:
                    {"success": False, "error": <reason>}
    
        Constraints:
            - Document must exist.
            - user_id must exist and user must be authorized (e.g. permission includes 'review' or 'validate').
            - Reviewer comment is overwritten if already present.
        """
        # Check if user exists
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User does not exist."}

        # Commenting is allowed for review-capable staff and explicit write-comment staff.
        if not self._has_comment_permission(user):
            return {"success": False, "error": "User not authorized to comment on claim documents."}

        # Check if document exists
        doc = self.claim_documents.get(document_id)
        if not doc:
            return {"success": False, "error": "Claim document does not exist."}

        # Update comment
        doc["reviewer_comment"] = comment

        return {"success": True, "message": f"Reviewer comment updated on document {document_id}."}

    def assign_claim_reviewer(self, claim_id: str, reviewer_id: str) -> dict:
        """
        Assign or re-assign a claim to an internal reviewer.

        Args:
            claim_id (str): The ID of the claim to be assigned.
            reviewer_id (str): The user ID of the reviewer.

        Returns:
            dict: {
                "success": True,
                "message": str  # Success message describing the assignment
            }
            or
            {
                "success": False,
                "error": str  # Description of the error
            }

        Constraints:
            - claim_id must exist in the system.
            - reviewer_id must exist in the system.
            - The user must have permission/role to act as a reviewer.
        """
        claim = self.claims.get(claim_id)
        if not claim:
            return { "success": False, "error": f"Claim {claim_id} does not exist." }

        reviewer = self.users.get(reviewer_id)
        if not reviewer:
            return { "success": False, "error": f"Reviewer {reviewer_id} does not exist." }

        # Example permission/role check: the user must have 'reviewer' in role or 'review' in permission
        reviewer_role = reviewer.get("role", "").lower()
        reviewer_permission = reviewer.get("permission", "").lower()
        if "reviewer" not in reviewer_role and "review" not in reviewer_permission:
            return { "success": False, "error": "User is not authorized to be assigned as a reviewer." }

        # Assign or re-assign
        self.claims[claim_id]["assigned_reviewer_id"] = reviewer_id

        return {
            "success": True,
            "message": f"Claim {claim_id} assigned to reviewer {reviewer_id}."
        }

    def update_claim_status(self, claim_id: str, new_status: str) -> dict:
        """
        Change the overall status of a claim (e.g., to 'approved', 'rejected', etc.),
        subject to document validity.

        Args:
            claim_id (str): The ID of the claim to update.
            new_status (str): The new status to set (e.g., "approved", "rejected").

        Returns:
            dict: {
              "success": True, "message": "Claim status updated to <new_status>"
            }
            or
            {
              "success": False, "error": "reason"
            }

        Constraints:
            - If new_status == "approved", each attached document_type must have at least
              one document whose validity_status == "valid".
            - The claim must exist.
            - If there are no claim documents, can't approve the claim.
        """
        if claim_id not in self.claims:
            return {"success": False, "error": "Claim does not exist"}

        # If setting to 'approved', require at least one valid document per document_type.
        if new_status.lower() == "approved":
            docs = [
                doc for doc in self.claim_documents.values()
                if doc["claim_id"] == claim_id
            ]
            if not docs:
                return {
                    "success": False,
                    "error": "Cannot approve claim: No documents attached to this claim."
                }
            docs_by_type = {}
            for doc in docs:
                docs_by_type.setdefault(doc["document_type"], []).append(doc)

            for document_type, typed_docs in docs_by_type.items():
                if not any(doc.get("validity_status", "").lower() == "valid" for doc in typed_docs):
                    return {
                        "success": False,
                        "error": f"Cannot approve claim: No valid document for type '{document_type}'."
                    }

        # All checks passed, update claim status
        self.claims[claim_id]["status"] = new_status
        return {
            "success": True,
            "message": f"Claim status updated to {new_status}"
        }

    def delete_claim_document(self, document_id: str, user_id: str) -> dict:
        """
        Remove a document from a claim, only if requested by an admin user or a user with sufficient permissions.

        Args:
            document_id (str): The unique ID of the claim document to delete.
            user_id (str): The ID of the user requesting the deletion.

        Returns:
            dict:
                - On success: { "success": True, "message": "Claim document <document_id> deleted." }
                - On failure: { "success": False, "error": "reason" }

        Constraints:
            - The specified document must exist.
            - The specified user must exist and be authorized (e.g., have 'admin' role or sufficient permissions).
            - The document is removed from the claim_documents mapping.
        """
        # Check if user exists
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }

        # Allow admin-capable staff and users with explicit delete permission strings.
        if not self._has_delete_permission(user):
            return { "success": False, "error": "Permission denied: unauthorized user" }

        # Check document existence
        if document_id not in self.claim_documents:
            return { "success": False, "error": "Claim document not found" }

        # Remove the document
        del self.claim_documents[document_id]

        return { "success": True, "message": f"Claim document {document_id} deleted." }


class InsuranceClaimProcessingSystem(BaseEnv):
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

    def get_customer_by_id(self, **kwargs):
        return self._call_inner_tool('get_customer_by_id', kwargs)

    def list_claims_by_customer(self, **kwargs):
        return self._call_inner_tool('list_claims_by_customer', kwargs)

    def get_claim_by_id(self, **kwargs):
        return self._call_inner_tool('get_claim_by_id', kwargs)

    def list_documents_by_claim(self, **kwargs):
        return self._call_inner_tool('list_documents_by_claim', kwargs)

    def get_document_by_type_and_filename(self, **kwargs):
        return self._call_inner_tool('get_document_by_type_and_filename', kwargs)

    def get_document_by_id(self, **kwargs):
        return self._call_inner_tool('get_document_by_id', kwargs)

    def check_document_validity_status(self, **kwargs):
        return self._call_inner_tool('check_document_validity_status', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def check_user_permission(self, **kwargs):
        return self._call_inner_tool('check_user_permission', kwargs)

    def list_claim_documents_by_status(self, **kwargs):
        return self._call_inner_tool('list_claim_documents_by_status', kwargs)

    def get_claim_status(self, **kwargs):
        return self._call_inner_tool('get_claim_status', kwargs)

    def upload_claim_document(self, **kwargs):
        return self._call_inner_tool('upload_claim_document', kwargs)

    def validate_claim_document(self, **kwargs):
        return self._call_inner_tool('validate_claim_document', kwargs)

    def add_reviewer_comment_to_document(self, **kwargs):
        return self._call_inner_tool('add_reviewer_comment_to_document', kwargs)

    def assign_claim_reviewer(self, **kwargs):
        return self._call_inner_tool('assign_claim_reviewer', kwargs)

    def update_claim_status(self, **kwargs):
        return self._call_inner_tool('update_claim_status', kwargs)

    def delete_claim_document(self, **kwargs):
        return self._call_inner_tool('delete_claim_document', kwargs)
