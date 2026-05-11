# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



class CompanyInfo(TypedDict):
    company_id: str
    name: str
    performance_id: str
    industry: str
    sta: str  # Status or code—exact meaning assumed from context

class FinancialDocumentInfo(TypedDict):
    document_id: str
    company_id: str
    document_type: str
    period_type: str
    period_start_date: str
    period_end_date: str
    version: str  # Could be represented as int if versions are numeric
    issued_date: str
    status: str
    conten: str   # Assuming typo for 'content'

class DocumentVersionInfo(TypedDict):
    document_id: str
    version: str
    change_description: str
    updated_by: str
    update_timestamp: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment state for an enterprise financial reporting system.
        """

        # Companies: {company_id: CompanyInfo}
        self.companies: Dict[str, CompanyInfo] = {}  # Maps company_id to company details

        # Financial Documents: {document_id: FinancialDocumentInfo}
        self.financial_documents: Dict[str, FinancialDocumentInfo] = {}  # Maps document_id to document

        # Document Versions: {document_id: List[DocumentVersionInfo]}
        self.document_versions: Dict[str, List[DocumentVersionInfo]] = {}  # Version history per document

        # Constraints:
        # - Each FinancialDocument must be associated with a valid company_id.
        # - No two FinancialDocuments for the same company, document_type, period_type, and period (start/end dates) can share the same version.
        # - Only the most recent version of a document is considered current unless specifically querying for a different version.
        # - Document status may include: draft, finalized, restated.

    @staticmethod
    def _version_sort_key(version_value):
        if isinstance(version_value, str):
            stripped = version_value.strip()
            if stripped.isdigit():
                return (0, int(stripped))
            prefix = "".join(ch for ch in stripped if not ch.isdigit())
            digits = "".join(ch for ch in stripped if ch.isdigit())
            if digits:
                return (1, prefix.lower(), int(digits))
            return (2, stripped.lower())
        return (3, str(version_value))

    def _matching_document_entries(self, document_id: str):
        matches = []
        for storage_key, doc in self.financial_documents.items():
            if storage_key == document_id or doc.get("document_id") == document_id:
                matches.append((storage_key, doc))
        return matches

    def _resolve_document_entry(self, document_id: str, version: str = None):
        matches = self._matching_document_entries(document_id)
        if version is not None:
            for storage_key, doc in matches:
                if doc.get("version") == version:
                    return storage_key, doc
            return None, None
        if not matches:
            return None, None
        return max(matches, key=lambda item: self._version_sort_key(item[1].get("version", "")))

    def get_company_by_performance_id(self, performance_id: str) -> dict:
        """
        Retrieve company information using its performance_id.

        Args:
            performance_id (str): The performance identifier of the target company.

        Returns:
            dict: {
                "success": True,
                "data": CompanyInfo  # The company info associated with the given performance_id
            }
            or
            {
                "success": False,
                "error": str  # Description of why the company could not be found
            }

        Constraints:
            - performance_id must match exactly to a company's stored performance_id.
        """
        for company_info in self.companies.values():
            if company_info["performance_id"] == performance_id:
                return { "success": True, "data": company_info }
        return { "success": False, "error": f"No company found with performance_id '{performance_id}'." }

    def get_company_by_id(self, company_id: str) -> dict:
        """
        Retrieve company information using company_id.

        Args:
            company_id (str): The unique identifier of the company.

        Returns:
            dict:
            - On success: { "success": True, "data": CompanyInfo }
            - On failure: { "success": False, "error": "Company not found" }

        Constraints:
            - company_id must exist in the system.
        """
        company = self.companies.get(company_id)
        if company is None:
            return { "success": False, "error": "Company not found" }
        return { "success": True, "data": company }

    def list_companies(self) -> dict:
        """
        Retrieve a list of all companies in the system.
    
        Args:
            None

        Returns:
            dict: 
                success: True if operation successful, always in this context
                data: List[CompanyInfo] containing all companies (possibly empty)
        """
        companies_list = list(self.companies.values())
        return { "success": True, "data": companies_list }

    def get_financial_documents_by_company(self, company_id: str) -> dict:
        """
        List all financial documents associated with a given company_id.

        Args:
            company_id (str): The unique identifier for the company.

        Returns:
            dict: 
                - success True: {"success": True, "data": List[FinancialDocumentInfo]} (possibly empty)
                - success False: {"success": False, "error": str}

        Constraints:
            - company_id must exist in self.companies.
        """
        if company_id not in self.companies:
            return {"success": False, "error": "Company does not exist."}
    
        docs = [
            doc for doc in self.financial_documents.values()
            if doc.get("company_id") == company_id
        ]
        return {"success": True, "data": docs}

    def find_financial_document(
        self,
        company_id: str,
        document_type: str,
        period_type: str,
        period_start_date: str,
        period_end_date: str
    ) -> dict:
        """
        Retrieve the most recent version of a financial document filtered by company_id,
        document_type, period_type, period_start_date, and period_end_date.

        Args:
            company_id (str): Unique ID of the company.
            document_type (str): Type of the document (e.g., 'balance_sheet').
            period_type (str): Reporting period type ('annual', 'quarterly', etc.).
            period_start_date (str): Start date of the period.
            period_end_date (str): End date of the period.

        Returns:
            dict:
                {
                    "success": True,
                    "data": FinancialDocumentInfo
                }
                or
                {
                    "success": False,
                    "error": str  # Error message
                }

        Constraints:
            - The company_id must exist.
            - Multiple versions: the most recent one (largest version) is returned.
        """
        if company_id not in self.companies:
            return { "success": False, "error": "Company not found" }

        # Filter by all required fields
        candidates = [
            doc for doc in self.financial_documents.values()
            if doc["company_id"] == company_id
            and doc["document_type"] == document_type
            and doc["period_type"] == period_type
            and doc["period_start_date"] == period_start_date
            and doc["period_end_date"] == period_end_date
        ]

        if not candidates:
            return { "success": False, "error": "Financial document not found" }

        # Select the "most recent" version according to version field
        # Return document with highest version
        latest_doc = max(candidates, key=lambda doc: self._version_sort_key(doc.get("version", "")))
        return { "success": True, "data": latest_doc }

    def get_latest_financial_document(
        self,
        company_id: str,
        document_type: str,
        period_type: str,
        period_start_date: str,
        period_end_date: str
    ) -> dict:
        """
        Retrieve the most recent version of a specified type of financial document 
        for a company and reporting period.

        Args:
            company_id (str): The target company's identifier.
            document_type (str): The type of financial document (e.g., 'Balance Sheet').
            period_type (str): The type of period (e.g., 'annual', 'quarterly').
            period_start_date (str): Reporting period start date (format: 'YYYY-MM-DD').
            period_end_date (str): Reporting period end date (format: 'YYYY-MM-DD').

        Returns:
            dict: 
              On success: { "success": True, "data": FinancialDocumentInfo }
              On failure: { "success": False, "error": str }

        Constraints:
            - company_id must exist.
            - Must select document with the highest version for the given keys.
        """
        # Check company exists
        if company_id not in self.companies:
            return {"success": False, "error": f"Company {company_id} does not exist"}

        # Filter relevant documents
        matched_docs = [
            doc for doc in self.financial_documents.values()
            if (
                doc["company_id"] == company_id and
                doc["document_type"] == document_type and
                doc["period_type"] == period_type and
                doc["period_start_date"] == period_start_date and
                doc["period_end_date"] == period_end_date
            )
        ]
        if not matched_docs:
            return {"success": False, "error": "No matching financial documents found"}

        # Select document with latest version (assume version is string but compare numerically if possible)
        latest_doc = max(matched_docs, key=lambda doc: self._version_sort_key(doc.get("version", "")))

        return {"success": True, "data": latest_doc}

    def get_financial_documents_by_status(self, company_id: str, status: str) -> dict:
        """
        Retrieve all financial documents for a company by document status.

        Args:
            company_id (str): The unique identifier for the company.
            status (str): The desired document status to filter by (e.g., 'draft', 'finalized', 'restated').
                Status matching is case-insensitive.

        Returns:
            dict: {
                "success": True,
                "data": List[FinancialDocumentInfo]  # All documents for company with that status
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - company_id must exist in the system.
            - If no matching documents, returns empty data list.
        """
        if company_id not in self.companies:
            return {"success": False, "error": "Company does not exist."}

        status_lower = status.lower()
        result = [
            doc for doc in self.financial_documents.values()
            if doc["company_id"] == company_id and doc["status"].lower() == status_lower
        ]
        return {"success": True, "data": result}

    def get_financial_document_versions(self, document_id: str) -> dict:
        """
        Retrieve the full version history for a given financial document.

        Args:
            document_id (str): The unique identifier for the financial document.

        Returns:
            dict: {
                "success": True,
                "data": List[DocumentVersionInfo]  # List of version info dicts; may be empty if no versions
            }
            or
            {
                "success": False,
                "error": str  # Description of failure (e.g., document not found)
            }

        Constraints:
            - The document_id must correspond to an existing financial document.
        """
        if not self._matching_document_entries(document_id):
            return { "success": False, "error": "Financial document not found for the given document_id" }

        versions = self.document_versions.get(document_id, [])
        return { "success": True, "data": versions }

    def get_financial_document_by_version(self, document_id: str, version: str) -> dict:
        """
        Retrieve a specific version of a financial document by its document_id and version.

        Args:
            document_id (str): The unique ID of the financial document.
            version (str): The document version to retrieve.

        Returns:
            dict:
              - On success:
                { "success": True, "data": FinancialDocumentInfo }
              - On failure:
                { "success": False, "error": str }

        Constraints:
            - The document_id must exist.
            - The version must exist for that document.

        Notes:
            - Assumes that 'financial_documents' contains entries for all versions,
              or that document_id and version together uniquely identify the document.
        """
        # Find a financial document with this id and version
        found = None
        for doc in self.financial_documents.values():
            if doc["document_id"] == document_id and doc["version"] == version:
                found = doc
                break

        if found:
            return { "success": True, "data": found }
        else:
            # Distinguish between document not existing and version not existing for clearer error
            doc_ids = [doc for doc in self.financial_documents.values() if doc["document_id"] == document_id]
            if not doc_ids:
                return { "success": False, "error": "Document not found" }
            else:
                return { "success": False, "error": "Version not found for this document" }

    def get_financial_document_content(self, document_id: str, version: str = None) -> dict:
        """
        Retrieve the content of a financial document by document_id,
        and optionally, a specific version.
    
        Args:
            document_id (str): The ID of the financial document.
            version (str, optional): The version to retrieve.
                If not provided, retrieve the latest/current version.
    
        Returns:
            dict: If successful:
                { "success": True, "data": <content string> }
            If error:
                { "success": False, "error": <error message> }
    
        Constraints:
            - document_id must exist.
            - If version is provided, must exist for this document.
            - If version not provided, return the latest version (max version).
        """
        _, doc = self._resolve_document_entry(document_id, version=None)
        if not doc:
            return { "success": False, "error": f"Document with id '{document_id}' does not exist." }

        # If no version specified, return conten from the latest/current version
        if version is None or version == doc["version"]:
            return { "success": True, "data": doc.get("conten", "") }

        logical_document_id = doc.get("document_id", document_id)

        version_list = self.document_versions.get(logical_document_id, [])
        if not any(ver.get("version") == version for ver in version_list):
            # No such version
            return { "success": False, "error": f"Version '{version}' not found for document_id '{document_id}'." }

        _, versioned_doc = self._resolve_document_entry(logical_document_id, version=version)
        if versioned_doc:
            return { "success": True, "data": versioned_doc.get("conten", "") }
        else:
            # Version entry exists, but actual doc version content is missing
            return { "success": False, "error": f"Content for version '{version}' of document '{document_id}' not found." }

    def compare_financial_document_versions(
        self,
        document_id: str,
        version_a: str,
        version_b: str
    ) -> dict:
        """
        Compare two versions of the same financial document and list their differences.

        Args:
            document_id (str): ID of the financial document to compare.
            version_a (str): First version identifier.
            version_b (str): Second version identifier.

        Returns:
            dict: 
                On success:
                {
                    "success": True,
                    "data": {
                        "diff": dict,  # Field-wise difference, especially 'conten'
                        "version_a_info": FinancialDocumentInfo,
                        "version_b_info": FinancialDocumentInfo
                    }
                }
                On error:
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - Both versions must exist for the same document_id.
            - Diff produced on all differing fields, with focus on core fields and content.
        """
        # Find both versions for the document
        docs_a = [
            doc for doc in self.financial_documents.values()
            if doc["document_id"] == document_id and doc["version"] == version_a
        ]
        docs_b = [
            doc for doc in self.financial_documents.values()
            if doc["document_id"] == document_id and doc["version"] == version_b
        ]

        if not docs_a:
            return {
                "success": False,
                "error": f"Version {version_a} of document_id {document_id} not found"
            }
        if not docs_b:
            return {
                "success": False,
                "error": f"Version {version_b} of document_id {document_id} not found"
            }
    
        doc_a = docs_a[0]
        doc_b = docs_b[0]

        # Compare fields
        diff = {}
        keys = list(doc_a.keys())
        for key in keys:
            val_a = doc_a.get(key)
            val_b = doc_b.get(key)
            if val_a != val_b:
                diff[key] = {"version_a": val_a, "version_b": val_b}

        return {
            "success": True,
            "data": {
                "diff": diff,
                "version_a_info": doc_a,
                "version_b_info": doc_b
            }
        }

    def add_company(
        self,
        company_id: str,
        name: str,
        performance_id: str,
        industry: str,
        sta: str
    ) -> dict:
        """
        Add a new company to the registry.

        Args:
            company_id (str): Unique identifier for the company.
            name (str): Name of the company.
            performance_id (str): Performance identifier.
            industry (str): Industry code/name.
            sta (str): Company status code.

        Returns:
            dict:
                success (bool): True if operation successful, False otherwise.
                message (str): Description of success if successful.
                error (str): Reason for failure if not.

        Constraints:
            - company_id must be unique (not already present in registry).
        """
        if company_id in self.companies:
            return { "success": False, "error": "Company ID already exists." }
    
        company_info: CompanyInfo = {
            "company_id": company_id,
            "name": name,
            "performance_id": performance_id,
            "industry": industry,
            "sta": sta
        }
        self.companies[company_id] = company_info

        return { "success": True, "message": "Company added successfully." }

    def update_company_info(
        self, 
        company_id: str,
        name: str = None,
        performance_id: str = None,
        industry: str = None,
        sta: str = None
    ) -> dict:
        """
        Update details (name, performance_id, industry, status) for a company.

        Args:
            company_id (str): The unique identifier for the company to update.
            name (str, optional): New name for the company.
            performance_id (str, optional): New performance_id.
            industry (str, optional): New industry.
            sta (str, optional): New status or code.

        Returns:
            dict: {
                "success": True,
                "message": "Company info updated."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The company must exist in the system.
            - Only supplied fields are updated.
            - No update is performed if all arguments (except company_id) are None.
        """
        if company_id not in self.companies:
            return { "success": False, "error": "Company with given company_id does not exist." }

        company = self.companies[company_id]
        updated = False

        # Update fields if new values are provided
        if name is not None:
            company["name"] = name
            updated = True
        if performance_id is not None:
            company["performance_id"] = performance_id
            updated = True
        if industry is not None:
            company["industry"] = industry
            updated = True
        if sta is not None:
            company["sta"] = sta
            updated = True

        if updated:
            self.companies[company_id] = company
            return { "success": True, "message": "Company info updated." }
        else:
            return { "success": True, "message": "No fields updated." }

    def add_financial_document(
        self,
        document_id: str,
        company_id: str,
        document_type: str,
        period_type: str,
        period_start_date: str,
        period_end_date: str,
        version: str,
        issued_date: str,
        status: str,
        conten: str
    ) -> dict:
        """
        Add a new financial document to a company's record.

        Args:
            document_id (str): Unique identifier for the document.
            company_id (str): Identifier of the company; must exist.
            document_type (str): Type of financial document (e.g., balance sheet).
            period_type (str): Reporting period type (e.g., annual, quarterly).
            period_start_date (str): Start date of the reporting period.
            period_end_date (str): End date of the reporting period.
            version (str): Version identifier (original, restated, etc).
            issued_date (str): The issuance date for the document.
            status (str): Document status (draft, finalized, restated, etc).
            conten (str): Content of the financial document.

        Returns:
            dict: { "success": True, "message": "Financial document added." }
                  or
                  { "success": False, "error": "<reason>" }

        Constraints:
            - The company_id must exist.
            - document_id must be unique.
            - No existing document for the same (company_id, document_type, period_type, period_start_date, period_end_date, version).
        """
        # Check for valid company
        if company_id not in self.companies:
            return { "success": False, "error": "Company does not exist." }

        # Check for unique document_id
        if document_id in self.financial_documents:
            return { "success": False, "error": "Document ID already exists." }

        # Ensure uniqueness constraint for version etc.
        for doc in self.financial_documents.values():
            if (
                doc['company_id'] == company_id and
                doc['document_type'] == document_type and
                doc['period_type'] == period_type and
                doc['period_start_date'] == period_start_date and
                doc['period_end_date'] == period_end_date and
                doc['version'] == version
            ):
                return { "success": False, "error": "A document with the same company, type, period, and version already exists." }

        # Add document
        self.financial_documents[document_id] = {
            "document_id": document_id,
            "company_id": company_id,
            "document_type": document_type,
            "period_type": period_type,
            "period_start_date": period_start_date,
            "period_end_date": period_end_date,
            "version": version,
            "issued_date": issued_date,
            "status": status,
            "conten": conten
        }

        return { "success": True, "message": "Financial document added." }

    def update_financial_document(
        self,
        document_id: str,
        updates: dict,
        change_description: str = "",
        updated_by: str = "",
        update_timestamp: str = "",
    ) -> dict:
        """
        Update (e.g., restate, amend) an existing financial document for a company.

        Args:
            document_id (str): The unique identifier of the financial document to update.
            updates (dict): Dictionary of fields to update and their new values (e.g. status, conten, period dates, version).
            change_description (str): Description of the change (for audit/version history).
            updated_by (str): Username or identifier of who performed the update.
            update_timestamp (str): When the update occurred (ISO string).

        Returns:
            dict: {
                "success": True,
                "message": "Financial document updated successfully"
            }
            or
            {
                "success": False,
                "error": str  # Description of why update failed
            }

        Constraints:
            - Document must exist.
            - Updated company_id must exist if provided.
            - For the same company, document_type, period_type, period (start/end), no duplicate version.
            - All updates must respect state space and system rules.
            - On significant update, a DocumentVersion record is created.
        """

        storage_key, doc = self._resolve_document_entry(document_id)
        if not doc:
            return { "success": False, "error": "Document does not exist" }

        # If changing company_id, ensure new one exists.
        if "company_id" in updates:
            new_company_id = updates["company_id"]
            if new_company_id not in self.companies:
                return { "success": False, "error": "New company_id does not exist" }

        # Check uniqueness constraint if document_type, period, period_type, version, company_id could change
        uniq_keys = ["company_id", "document_type", "period_type", "period_start_date", "period_end_date", "version"]
        will_violate = False
        for fid, fdoc in self.financial_documents.items():
            if fid == storage_key:
                continue  # Skip the resolved stored version being updated
            # Prepare candidate new values
            comp = {}
            for key in uniq_keys:
                comp[key] = updates.get(key, doc[key])
            # If all keys match, that's a uniqueness conflict!
            same = all(comp[k] == fdoc[k] for k in uniq_keys)
            if same:
                will_violate = True
                break
        if will_violate:
            return { "success": False, "error": "Update would violate uniqueness constraint for versioning" }

        # Prepare update log for DocumentVersion if applicable
        significant_fields = set(updates.keys()) & set(["conten", "status", "period_start_date", "period_end_date", "version"])
        if significant_fields and change_description:
            version_entry = {
                "document_id": doc.get("document_id", document_id),
                "version": updates.get("version", doc["version"]),
                "change_description": change_description,
                "updated_by": updated_by,
                "update_timestamp": update_timestamp,
            }
            self.document_versions.setdefault(doc.get("document_id", document_id), []).append(version_entry)

        # Update document fields
        for k, v in updates.items():
            if k == "document_id":
                continue  # Cannot change document_id
            if k in doc:
                doc[k] = v

        self.financial_documents[storage_key] = doc

        return { "success": True, "message": "Financial document updated successfully" }

    def change_financial_document_status(self, document_id: str, new_status: str) -> dict:
        """
        Change the status of a financial document (e.g., from draft to finalized or restated).

        Args:
            document_id (str): Unique identifier of the financial document.
            new_status (str): The new status to set ("draft", "finalized", or "restated").

        Returns:
            dict: On success: { "success": True, "message": "Status updated successfully." }
                  On failure: { "success": False, "error": "reason" }

        Constraints:
            - The document must exist.
            - Status can only be one of: "draft", "finalized", "restated".
        """
        allowed_statuses = {"draft", "finalized", "restated"}

        storage_key, doc = self._resolve_document_entry(document_id)
        if doc is None:
            return { "success": False, "error": "Financial document does not exist." }
    
        if new_status not in allowed_statuses:
            return { "success": False, "error": f"Invalid status '{new_status}'. Allowed statuses: draft, finalized, restated." }

        doc["status"] = new_status
        self.financial_documents[storage_key] = doc

        return { "success": True, "message": f"Financial document status updated to '{new_status}'." }

    def add_document_version(self, document_id: str, version: str, change_description: str, updated_by: str, update_timestamp: str) -> dict:
        """
        Append a new version to a financial document's version history.

        Args:
            document_id (str): The target document's identifier.
            version (str): The new version identifier.
            change_description (str): Explanation of the changes in this version.
            updated_by (str): Who updated/made the change.
            update_timestamp (str): Timestamp of the update (string).

        Returns:
            dict:
                - On success: {
                    "success": True,
                    "message": "Version appended to document version history"
                }
                - On failure: {
                    "success": False,
                    "error": "reason"
                }

        Constraints:
            - The document_id must exist in the financial_documents.
            - No duplicate version for same document_id.
        """
        # Check document existence
        _, doc = self._resolve_document_entry(document_id)
        if not doc:
            return { "success": False, "error": "Document does not exist" }

        logical_document_id = doc.get("document_id", document_id)

        # Initialize version history if missing
        if logical_document_id not in self.document_versions:
            self.document_versions[logical_document_id] = []

        # Check for duplicate version
        for ver in self.document_versions[logical_document_id]:
            if ver["version"] == version:
                return { "success": False, "error": "Version already exists for this document" }

        # Append new version info
        new_version_info = {
            "document_id": logical_document_id,
            "version": version,
            "change_description": change_description,
            "updated_by": updated_by,
            "update_timestamp": update_timestamp
        }
        self.document_versions[logical_document_id].append(new_version_info)
        return { "success": True, "message": "Version appended to document version history" }

    def remove_financial_document(self, document_id: str) -> dict:
        """
        Remove a financial document and any associated document versions from the system.

        Args:
            document_id (str): The unique identifier for the financial document.

        Returns:
            dict: {
                "success": True,
                "message": "Financial document <document_id> and its versions removed."
            }
            OR
            {
                "success": False,
                "error": "Financial document not found."
            }

        Constraints:
            - If the document does not exist, operation fails (no partial action).
            - All version history linked to this document_id is deleted as well (if present).
        """

        matches = self._matching_document_entries(document_id)
        if not matches:
            return { "success": False, "error": "Financial document not found." }

        logical_document_id = matches[0][1].get("document_id", document_id)

        for storage_key, _ in matches:
            del self.financial_documents[storage_key]

        if logical_document_id in self.document_versions:
            del self.document_versions[logical_document_id]

        return {
            "success": True,
            "message": f"Financial document {document_id} and its versions removed."
        }


class EnterpriseFinancialReportingSystem(BaseEnv):
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

    def get_company_by_performance_id(self, **kwargs):
        return self._call_inner_tool('get_company_by_performance_id', kwargs)

    def get_company_by_id(self, **kwargs):
        return self._call_inner_tool('get_company_by_id', kwargs)

    def list_companies(self, **kwargs):
        return self._call_inner_tool('list_companies', kwargs)

    def get_financial_documents_by_company(self, **kwargs):
        return self._call_inner_tool('get_financial_documents_by_company', kwargs)

    def find_financial_document(self, **kwargs):
        return self._call_inner_tool('find_financial_document', kwargs)

    def get_latest_financial_document(self, **kwargs):
        return self._call_inner_tool('get_latest_financial_document', kwargs)

    def get_financial_documents_by_status(self, **kwargs):
        return self._call_inner_tool('get_financial_documents_by_status', kwargs)

    def get_financial_document_versions(self, **kwargs):
        return self._call_inner_tool('get_financial_document_versions', kwargs)

    def get_financial_document_by_version(self, **kwargs):
        return self._call_inner_tool('get_financial_document_by_version', kwargs)

    def get_financial_document_content(self, **kwargs):
        return self._call_inner_tool('get_financial_document_content', kwargs)

    def compare_financial_document_versions(self, **kwargs):
        return self._call_inner_tool('compare_financial_document_versions', kwargs)

    def add_company(self, **kwargs):
        return self._call_inner_tool('add_company', kwargs)

    def update_company_info(self, **kwargs):
        return self._call_inner_tool('update_company_info', kwargs)

    def add_financial_document(self, **kwargs):
        return self._call_inner_tool('add_financial_document', kwargs)

    def update_financial_document(self, **kwargs):
        return self._call_inner_tool('update_financial_document', kwargs)

    def change_financial_document_status(self, **kwargs):
        return self._call_inner_tool('change_financial_document_status', kwargs)

    def add_document_version(self, **kwargs):
        return self._call_inner_tool('add_document_version', kwargs)

    def remove_financial_document(self, **kwargs):
        return self._call_inner_tool('remove_financial_document', kwargs)
