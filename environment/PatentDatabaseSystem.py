# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
from typing import List, Optional, Dict, Any



class PatentInfo(TypedDict):
    # State mapping: Patent
    patent_id: str
    title: str
    filing_date: str
    publication_date: str
    abstract: str
    status: str
    classification_codes: List[str]  # List of ClassificationCode.code
    assignee_ids: List[str]          # List of Assignee.assignee_id
    inventor_id: str                 # Inventor.inventor_id

class ClassificationCodeInfo(TypedDict):
    # State mapping: ClassificationCode
    code: str
    description: str
    type: str  # e.g., USPC, IPC, CPC

class AssigneeInfo(TypedDict):
    # State mapping: Assignee
    assignee_id: str
    name: str
    type: str         # individual / organization
    address: str

class InventorInfo(TypedDict):
    # State mapping: Inventor
    inventor_id: str
    name: str
    address: str
    nationality: str

class _GeneratedEnvImpl:
    def __init__(self):
        # ===== State dictionaries =====
        # Patents: {patent_id: PatentInfo}
        self.patents: Dict[str, PatentInfo] = {}
        # Classification codes: {code: ClassificationCodeInfo}
        self.classification_codes: Dict[str, ClassificationCodeInfo] = {}
        # Assignees: {assignee_id: AssigneeInfo}
        self.assignees: Dict[str, AssigneeInfo] = {}
        # Inventors: {inventor_id: InventorInfo}
        self.inventors: Dict[str, InventorInfo] = {}

        # ===== Constraints & Rules (See constraints_rules input) =====
        # - Each Patent can have multiple ClassificationCodes and Assignees.
        # - Patents cannot exist without at least one classification code.
        # - Data integrity must be maintained: patent-assignee and patent-classification relationships must be valid.
        # - Searches must support filtering by any combination of classification codes, dates, assignee names, etc.
        # - Titles and assignee names must be retrievable and sortable for search results.

    def _patent_for_output(self, patent: PatentInfo) -> Dict[str, Any]:
        patent_view = dict(patent)
        patent_view["assignee_names"] = [
            self.assignees[assignee_id]["name"]
            for assignee_id in patent.get("assignee_ids", [])
            if assignee_id in self.assignees
        ]
        return patent_view


    def search_patents(
        self,
        classification_codes: Optional[List[str]] = None,
        filing_date_from: Optional[str] = None,
        filing_date_to: Optional[str] = None,
        publication_date_from: Optional[str] = None,
        publication_date_to: Optional[str] = None,
        assignee_ids: Optional[List[str]] = None,
        assignee_names: Optional[List[str]] = None,
        inventor_ids: Optional[List[str]] = None,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve patents filtered by any combination of:
            - classification_codes: List of classification code strings (intersection: patent must have at least one)
            - filing_date_from / filing_date_to: Only patents with filing_date >= from and/or <= to (ISO string)
            - publication_date_from / publication_date_to: Only patents with publication_date >= from and/or <= to
            - assignee_ids: list of IDs (patent must have at least one in this list)
            - assignee_names: list of names (maps to IDs)
            - inventor_ids: list of inventor_id values
            - status: legal status string

        All parameters are optional. If none are given, returns all patents.

        Returns:
            dict with keys:
                - success (bool)
                - data (list of PatentInfo dicts) on success
                - error (str) on failure

        Constraints:
            - For assignee_names, matches are case-sensitive.
            - Dates should be in comparable-string format (YYYY-MM-DD).
        """
        # Prepare assignee_id lookup for supplied assignee_names
        assignee_name_id_map = {}
        if assignee_names:
            for assignee in self.assignees.values():
                if assignee["name"] in assignee_names:
                    assignee_name_id_map.setdefault(assignee["name"], []).append(assignee["assignee_id"])
            # Flatten all found IDs
            assignee_ids_from_names = [
                assignee_id
                for name in assignee_names
                for assignee_id in assignee_name_id_map.get(name, [])
            ]
            # If an assignee_name doesn't exist, no patent will match it (so leave empty list)
            if assignee_ids is not None:
                combined_assignee_ids = set(assignee_ids) | set(assignee_ids_from_names)
            else:
                combined_assignee_ids = set(assignee_ids_from_names)
        else:
            combined_assignee_ids = set(assignee_ids) if assignee_ids is not None else None

        result = []
        for patent in self.patents.values():
            # Filter by classification_codes
            if classification_codes is not None and not set(classification_codes) & set(patent["classification_codes"]):
                continue
            # Filter by filing date
            if filing_date_from is not None and patent["filing_date"] < filing_date_from:
                continue
            if filing_date_to is not None and patent["filing_date"] > filing_date_to:
                continue
            # Filter by publication date
            if publication_date_from is not None and patent["publication_date"] < publication_date_from:
                continue
            if publication_date_to is not None and patent["publication_date"] > publication_date_to:
                continue
            # Filter by assignee_ids (including those resolved from names)
            if combined_assignee_ids is not None:
                if not set(patent["assignee_ids"]) & combined_assignee_ids:
                    continue
            # Filter by inventor_ids
            if inventor_ids is not None and patent["inventor_id"] not in inventor_ids:
                continue
            # Filter by status
            if status is not None and patent["status"] != status:
                continue
            # All filters passed
            result.append(self._patent_for_output(patent))

        return {"success": True, "data": result}

    def get_patent_by_id(self, patent_id: str) -> dict:
        """
        Retrieve the complete information of a patent given its patent_id.

        Args:
            patent_id (str): The unique identifier of the desired patent.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": PatentInfo  # all fields for the patent
                    }
                On failure (not found):
                    {
                        "success": False,
                        "error": "Patent not found"
                    }

        Constraints:
            - Only returns patents present in the database.
            - Patent relationships are not validated during this operation.
        """
        patent = self.patents.get(patent_id)
        if not patent:
            return {"success": False, "error": "Patent not found"}

        return {"success": True, "data": self._patent_for_output(patent)}

    def list_patent_titles(
        self,
        classification_codes: list = None,
        assignee_names: list = None,
        status: str = None,
        filing_date_range: tuple = None,
        sort_by: str = "title",
        ascending: bool = True
    ) -> dict:
        """
        Retrieve and optionally sort the titles of patents, with filtering support.

        Args:
            classification_codes (list[str], optional): Only include patents having at least one of these codes.
            assignee_names (list[str], optional): Only include patents with at least one assignee matching these names.
            status (str, optional): Filter patents by status (e.g., 'granted', 'pending').
            filing_date_range (tuple(str, str), optional): (start_date, end_date), as ISO format 'YYYY-MM-DD'.
            sort_by (str, optional): Field to sort by ('title', 'filing_date', etc.), default is 'title'.
            ascending (bool, optional): Sort order; True for ascending (default), False for descending.

        Returns:
            dict: {
                "success": True,
                "data": List[str],  # Sorted, filtered list of patent titles.
            }
            or
            {
                "success": False,
                "error": str  # Error message if parameters invalid, etc.
            }
        Constraints:
            - Titles and assignee names are retrievable and results are sortable.
            - Filters are combined with AND logic.
        """
        # Input validation
        if sort_by not in {"title", "filing_date", "publication_date", "status"}:
            sort_by = "title"

        try:
            filtered_patents = list(self.patents.values())

            if classification_codes:
                filtered_patents = [
                    p for p in filtered_patents
                    if any(code in p["classification_codes"] for code in classification_codes)
                ]

            if assignee_names:
                # Find matching assignee_ids for the given names
                name_to_id = {a["name"]: a["assignee_id"] for a in self.assignees.values()}
                target_ids = {aid for name, aid in name_to_id.items() if name in assignee_names}
                filtered_patents = [
                    p for p in filtered_patents
                    if any(aid in target_ids for aid in p["assignee_ids"])
                ]

            if status:
                filtered_patents = [
                    p for p in filtered_patents
                    if p["status"] == status
                ]

            if filing_date_range:
                start, end = filing_date_range
                filtered_patents = [
                    p for p in filtered_patents
                    if start <= p["filing_date"] <= end
                ]

            # Sorting
            filtered_patents.sort(
                key=lambda p: p.get(sort_by, "").lower() if isinstance(p.get(sort_by, ""), str) else p.get(sort_by, ""),
                reverse=not ascending
            )

            titles = [p["title"] for p in filtered_patents]
            return {"success": True, "data": titles}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {str(e)}"}

    def get_patent_assignee_ids(self, patent_id: str) -> dict:
        """
        Get the list of assignee_id(s) assigned to a particular patent.

        Args:
            patent_id (str): Unique identifier for the patent.

        Returns:
            dict: {
                "success": True,
                "data": List[str],  # List of assignee_id(s), may be empty if none
            }
            or
            {
                "success": False,
                "error": str  # "Patent not found" if the patent_id does not exist
            }

        Constraints:
            - patent_id must exist in the database.
            - Returns the assignee IDs as listed in the patent record.
        """
        patent = self.patents.get(patent_id)
        if not patent:
            return { "success": False, "error": "Patent not found" }
        # Assignee_ids is a list as per schema, may be empty
        return { "success": True, "data": list(patent.get("assignee_ids", [])) }

    def get_assignee_by_id(self, assignee_id: str) -> dict:
        """
        Retrieve full details of an assignee by their assignee_id.

        Args:
            assignee_id (str): The unique identifier of the assignee.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": AssigneeInfo
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Assignee not found"
                    }
        Constraints:
            - assignee_id must exist in the system.
        """
        assignee = self.assignees.get(assignee_id)
        if assignee is None:
            return {"success": False, "error": "Assignee not found"}
        return {"success": True, "data": assignee}

    def get_assignee_name_by_id(self, assignee_id: str) -> dict:
        """
        Returns the name of an assignee given their assignee_id.

        Args:
            assignee_id (str): The unique identifier of the assignee.

        Returns:
            dict: {
                "success": True,
                "data": str  # The name of the assignee
            }
            OR
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The assignee_id must exist in the system.
        """
        assignee = self.assignees.get(assignee_id)
        if not assignee:
            return {"success": False, "error": "Assignee not found"}
        return {"success": True, "data": assignee["name"]}

    def list_patents_by_classification_code(self, classification_code: str) -> dict:
        """
        Retrieve all patents associated with a specific classification code.

        Args:
            classification_code (str): The code to filter patents by.

        Returns:
            dict:
                - On success:
                    { "success": True, "data": List[PatentInfo] }
                - On error:
                    { "success": False, "error": str }

        Constraints:
            - Provided classification_code must exist in the database.
            - Results may be empty if no patents are associated with the classification code.
        """
        if classification_code not in self.classification_codes:
            return { "success": False, "error": "Classification code does not exist" }

        result = [
            patent_info for patent_info in self.patents.values()
            if classification_code in patent_info["classification_codes"]
        ]

        return { "success": True, "data": result }

    def list_classification_codes(self) -> dict:
        """
        Retrieve and describe all patent classification codes in the database.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[ClassificationCodeInfo],  # All classification codes (could be empty)
            }
            or
            {
                "success": False,
                "error": str  # Error description
            }

        Constraints:
            - None (simple retrieval, no relationship checks)
        """
        codes = list(self.classification_codes.values())
        return { "success": True, "data": codes }

    def get_patent_classification_codes(self, patent_id: str) -> dict:
        """
        Retrieves the list of classification codes (with details) assigned to a particular patent.

        Args:
            patent_id (str): The unique identifier of the patent.

        Returns:
            dict: {
                "success": True,
                "data": List[ClassificationCodeInfo]
            }
            or
            {
                "success": False,
                "error": str  # Reason the operation failed
            }

        Constraints:
            - The patent must exist in the database.
            - Each classification code listed for a patent should exist in the classification_codes dictionary.
        """
        if patent_id not in self.patents:
            return { "success": False, "error": "Patent not found" }

        code_list = self.patents[patent_id].get("classification_codes", [])
        # Defensive: Return only existing code infos
        code_info_list = []
        for code in code_list:
            if code in self.classification_codes:
                code_info_list.append(self.classification_codes[code])
            else:
                # Data integrity violation, skip or could log
                continue

        return { "success": True, "data": code_info_list }

    def list_patents_by_assignee_id(self, assignee_id: str) -> dict:
        """
        Retrieve all patents (PatentInfo) associated with the given assignee_id.

        Args:
            assignee_id (str): The unique ID of the assignee.

        Returns:
            dict: {
                "success": True,
                "data": [PatentInfo, ...]  # List of PatentInfo dicts for all matching patents (may be empty if none)
            }
            or
            {
                "success": False,
                "error": str  # "Assignee does not exist"
            }

        Constraints:
            - assignee_id must exist in the database.
            - Only patents where assignee_id is present in patent["assignee_ids"] are returned.
        """
        if assignee_id not in self.assignees:
            return { "success": False, "error": "Assignee does not exist" }

        results = [
            patent for patent in self.patents.values()
            if assignee_id in patent.get("assignee_ids", [])
        ]
        return { "success": True, "data": results }

    def list_assignees(
        self,
        name: str = None,
        type: str = None,
        sort_by: str = "name",
        ascending: bool = True
    ) -> dict:
        """
        List all assignees, with optional filtering and sorting.
    
        Args:
            name (str, optional): Filter assignees by exact name.
            type (str, optional): Filter assignees by type ("individual" or "organization").
            sort_by (str, optional): Sort results by this field ("name", "assignee_id", "type", "address"). Defaults to "name".
            ascending (bool, optional): Sort order; True is ascending, False is descending. Defaults to True.
    
        Returns:
            dict: 
                - "success": True
                - "data": List of AssigneeInfo dicts (possibly empty)
            or
                - "success": False
                - "error": Reason for failure (e.g., invalid sort key)
    
        Constraints:
            - Filtering is exact match.
            - Sorting can be by one of the fields: "name", "assignee_id", "type", "address".
        """

        allowed_sort_keys = {"name", "assignee_id", "type", "address"}
        if sort_by not in allowed_sort_keys:
            return {"success": False, "error": f"Invalid sort key '{sort_by}'. Allowed keys: {sorted(allowed_sort_keys)}"}

        assignee_list = list(self.assignees.values())

        # Filtering
        if name is not None:
            assignee_list = [a for a in assignee_list if a["name"] == name]
        if type is not None:
            assignee_list = [a for a in assignee_list if a["type"] == type]

        # Sorting
        assignee_list.sort(key=lambda a: a[sort_by], reverse=not ascending)

        return {"success": True, "data": assignee_list}

    def list_inventors(
        self,
        filters: dict = None,
        sort_by: str = None,
        sort_order: str = "asc"
    ) -> dict:
        """
        List all inventors, with optional filtering and sorting.

        Args:
            filters (dict, optional): Keys can be any of:
                - 'inventor_id': exact match (str)
                - 'name': substring match (case-insensitive) (str)
                - 'address': substring match (case-insensitive) (str)
                - 'nationality': exact match (str)
            sort_by (str, optional): Attribute to sort by. One of 'inventor_id', 'name', 'address', 'nationality'.
            sort_order (str, optional): 'asc' (default) or 'desc'.

        Returns:
            dict: {
                "success": True,
                "data": List[InventorInfo]  # Filtered, sorted inventor records (may be empty)
            }
            or
            {
                "success": False,
                "error": str
            }
        """
        allowed_keys = {"inventor_id", "name", "address", "nationality"}

        if sort_by is not None and sort_by not in allowed_keys:
            return {
                "success": False,
                "error": f"Invalid sort_by key: {sort_by}"
            }
        if sort_order not in ("asc", "desc"):
            return {
                "success": False,
                "error": f"Invalid sort_order: {sort_order}"
            }

        filters = filters or {}

        for k in filters:
            if k not in allowed_keys:
                return {
                    "success": False,
                    "error": f"Invalid filter key: {k}"
                }

        def inventor_matches(inv: dict) -> bool:
            for k, v in filters.items():
                if k in ("name", "address"):
                    if v.lower() not in inv.get(k, "").lower():
                        return False
                else:  # inventor_id or nationality
                    if inv.get(k) != v:
                        return False
            return True

        matched = [inv for inv in self.inventors.values() if inventor_matches(inv)]

        if sort_by:
            matched.sort(
                key=lambda x: x.get(sort_by, ""),
                reverse=(sort_order == "desc")
            )

        return {
            "success": True,
            "data": matched
        }

    def get_inventor_by_id(self, inventor_id: str) -> dict:
        """
        Retrieve full details of an inventor by inventor_id.

        Args:
            inventor_id (str): The unique identifier for an Inventor.

        Returns:
            dict: {
                "success": True,
                "data": InventorInfo  # If inventor is found
            }
            or
            {
                "success": False,
                "error": str  # If inventor is not found
            }
        Constraints:
            - inventor_id must exist in the inventors database.
        """
        inventor = self.inventors.get(inventor_id)
        if inventor is None:
            return {"success": False, "error": "Inventor not found"}
        return {"success": True, "data": inventor}

    def add_patent(
        self,
        patent_id: str,
        title: str,
        filing_date: str,
        publication_date: str,
        abstract: str,
        status: str,
        classification_codes: list,
        assignee_ids: list,
        inventor_id: str
    ) -> dict:
        """
        Add a new patent entry, enforcing data integrity:
          - patent_id must be unique
          - At least one valid classification code required
          - All classification_codes must exist in the system
          - All assignee_ids must exist in the system
          - inventor_id must exist in the system

        Args:
            patent_id (str): New patent's unique identifier.
            title (str): Patent's title.
            filing_date (str): Filing date.
            publication_date (str): Publication date.
            abstract (str): Abstract.
            status (str): Status.
            classification_codes (List[str]): List of at least one classification code string.
            assignee_ids (List[str]): List of assignee IDs.
            inventor_id (str): Inventor's ID.

        Returns:
            dict: Success or error message.
        """

        # Check uniqueness of patent_id
        if patent_id in self.patents:
            return {"success": False, "error": f"Patent with id '{patent_id}' already exists."}

        # Must provide at least one classification code
        if not classification_codes or not isinstance(classification_codes, list):
            return {"success": False, "error": "At least one valid classification code must be provided."}
        # All codes must exist
        invalid_codes = [c for c in classification_codes if c not in self.classification_codes]
        if invalid_codes:
            return {"success": False, "error": f"Invalid classification code(s): {invalid_codes}"}

        # All assignee_ids must exist
        if not isinstance(assignee_ids, list):
            return {"success": False, "error": "assignee_ids must be a list."}
        invalid_assignees = [a for a in assignee_ids if a not in self.assignees]
        if invalid_assignees:
            return {"success": False, "error": f"Invalid assignee_id(s): {invalid_assignees}"}
    
        # inventor_id must exist
        if inventor_id not in self.inventors:
            return {"success": False, "error": f"Inventor id '{inventor_id}' does not exist."}

        # All checks passed, add patent
        self.patents[patent_id] = {
            "patent_id": patent_id,
            "title": title,
            "filing_date": filing_date,
            "publication_date": publication_date,
            "abstract": abstract,
            "status": status,
            "classification_codes": classification_codes,
            "assignee_ids": assignee_ids,
            "inventor_id": inventor_id
        }
        return {"success": True, "message": f"Patent {patent_id} successfully added."}

    def update_patent(self, patent_id: str, updates: dict) -> dict:
        """
        Update metadata or relationships (classification, assignee, inventor, etc.) for a given patent.

        Args:
            patent_id (str): The patent to update.
            updates (dict): Key-value pairs to update (e.g., any of the PatentInfo fields).
                - Valid keys: title, filing_date, publication_date, abstract, status,
                             classification_codes (List[str]), assignee_ids (List[str]), inventor_id (str)
        Returns:
            dict: 
                - Success: {"success": True, "message": "Patent updated successfully."}
                - Failure: {"success": False, "error": <reason>}
        Constraints:
            - New classification_codes must all exist and must not be empty.
            - New assignee_ids must each exist.
            - New inventor_id must exist.
            - patent_id must exist.
            - Only fields in PatentInfo can be updated.
        """
        # Check if patent exists
        patent = self.patents.get(patent_id)
        if not patent:
            return {"success": False, "error": "Patent does not exist."}

        # Validate updates
        allowed_fields = {
            "title", "filing_date", "publication_date",
            "abstract", "status", "classification_codes",
            "assignee_ids", "inventor_id"
        }

        for key in updates:
            if key not in allowed_fields:
                return {"success": False, "error": f"Unknown or uneditable field: {key}"}

        # If updating classification_codes
        if "classification_codes" in updates:
            codes = updates["classification_codes"]
            if not isinstance(codes, list) or len(codes) == 0:
                return {"success": False, "error": "Patent must have at least one classification code."}
            # All codes must exist
            for code in codes:
                if code not in self.classification_codes:
                    return {"success": False, "error": f"Classification code does not exist: {code}"}

        # If updating assignee_ids
        if "assignee_ids" in updates:
            aids = updates["assignee_ids"]
            if not isinstance(aids, list):
                return {"success": False, "error": "assignee_ids must be a list of assignee_id string(s)."}
            for aid in aids:
                if aid not in self.assignees:
                    return {"success": False, "error": f"Assignee does not exist: {aid}"}

        # If updating inventor_id
        if "inventor_id" in updates:
            inv = updates["inventor_id"]
            if inv not in self.inventors:
                return {"success": False, "error": f"Inventor does not exist: {inv}"}

        # All checks passed, perform update
        for key, value in updates.items():
            patent[key] = value

        self.patents[patent_id] = patent  # Save back (for mutability clarity)

        return {"success": True, "message": "Patent updated successfully."}

    def delete_patent(self, patent_id: str) -> dict:
        """
        Remove a patent and its relationships from the database.

        Args:
            patent_id (str): The unique identifier of the patent to delete.

        Returns:
            dict: 
                On success: { "success": True, "message": "Patent <patent_id> deleted." }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - The provided patent_id must exist in the database.
            - Only the patent record is removed; assignees, classification codes, and inventor records remain.
        """
        if patent_id not in self.patents:
            return { "success": False, "error": f"Patent {patent_id} does not exist." }

        del self.patents[patent_id]
        return { "success": True, "message": f"Patent {patent_id} deleted." }

    def add_assignee(self, assignee_id: str, name: str, type: str, address: str) -> dict:
        """
        Add a new assignee (individual or organization).

        Args:
            assignee_id (str): Unique identifier for the assignee.
            name (str): Name of the assignee.
            type (str): Type of assignee - must be "individual" or "organization".
            address (str): Address of the assignee.

        Returns:
            dict: {
                "success": True,
                "message": "Assignee added."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - assignee_id must be unique in the system.
            - type must be "individual" or "organization".
        """
        if assignee_id in self.assignees:
            return {"success": False, "error": "Assignee ID already exists."}
        if type not in ("individual", "organization"):
            return {"success": False, "error": "Assignee type must be 'individual' or 'organization'."}
        assignee_info: AssigneeInfo = {
            "assignee_id": assignee_id,
            "name": name,
            "type": type,
            "address": address
        }
        self.assignees[assignee_id] = assignee_info
        return {"success": True, "message": "Assignee added."}

    def update_assignee(
        self,
        assignee_id: str,
        name: str = None,
        type: str = None,
        address: str = None
    ) -> dict:
        """
        Update information for an existing assignee.

        Args:
            assignee_id (str): Unique identifier of the assignee to update.
            name (str, optional): New name for the assignee.
            type (str, optional): "individual" or "organization".
            address (str, optional): New address for the assignee.

        Returns:
            dict: {
                "success": True,
                "message": "Assignee updated successfully."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - assignee_id must exist.
            - At least one of name, type, or address must be provided.
            - If provided, type must be either "individual" or "organization".
        """
        if assignee_id not in self.assignees:
            return {"success": False, "error": "Assignee does not exist."}
        if name is None and type is None and address is None:
            return {"success": False, "error": "No update fields provided."}

        assignee = self.assignees[assignee_id]
        if type is not None:
            if type not in {"individual", "organization"}:
                return {"success": False, "error": "Assignee type must be 'individual' or 'organization'."}
            assignee["type"] = type
        if name is not None:
            assignee["name"] = name
        if address is not None:
            assignee["address"] = address

        self.assignees[assignee_id] = assignee
        return {"success": True, "message": "Assignee updated successfully."}

    def delete_assignee(self, assignee_id: str) -> dict:
        """
        Remove an assignee from the database, only if it is not referenced by any patent.

        Args:
            assignee_id (str): The ID of the assignee to delete.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Assignee deleted successfully"
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Error description
                    }

        Constraints:
            - Deletion is only possible if no patent references this assignee.
            - If the assignee does not exist, return an error.
        """

        # Check assignee existence
        if assignee_id not in self.assignees:
            return {"success": False, "error": "Assignee not found"}

        # Check for references in patents
        for patent in self.patents.values():
            if assignee_id in patent["assignee_ids"]:
                return {
                    "success": False,
                    "error": "Assignee is still referenced by one or more patents"
                }

        # Safe to delete
        del self.assignees[assignee_id]
        return {
            "success": True,
            "message": "Assignee deleted successfully"
        }

    def add_classification_code(self, code: str, description: str, type: str) -> dict:
        """
        Add a new classification code to the database.

        Args:
            code (str): Unique classification code.
            description (str): Description of the classification code.
            type (str): The classification type (e.g., USPC, IPC, CPC).

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Classification code added successfully" }
                On failure:
                    { "success": False, "error": "<reason>" }

        Constraints:
            - The classification code ('code') must be unique.
            - All parameters must be provided and non-empty.
        """
        # Input validation
        if not code or not isinstance(code, str) or not code.strip():
            return { "success": False, "error": "Parameter 'code' must be a non-empty string." }
        if not description or not isinstance(description, str) or not description.strip():
            return { "success": False, "error": "Parameter 'description' must be a non-empty string." }
        if not type or not isinstance(type, str) or not type.strip():
            return { "success": False, "error": "Parameter 'type' must be a non-empty string." }
    
        code = code.strip()
        if code in self.classification_codes:
            return { "success": False, "error": "Classification code already exists." }
    
        self.classification_codes[code] = {
            "code": code,
            "description": description.strip(),
            "type": type.strip(),
        }
        return { "success": True, "message": "Classification code added successfully" }

    def update_classification_code(
        self,
        code: str,
        description: str = None,
        type: str = None
    ) -> dict:
        """
        Update information (description, type) for an existing classification code.

        Args:
            code (str): The unique code identifier of the classification code to update.
            description (str, optional): New description for the classification code.
            type (str, optional): New type for the classification code (e.g., USPC, IPC, CPC).

        Returns:
            dict:
                On success: { "success": True, "message": "Classification code updated successfully." }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - The classification code ("code") must already exist in the system.
            - At least one of "description" or "type" must be provided.
            - The classification code's "code" field itself cannot be updated.
        """
        cc = self.classification_codes.get(code)
        if cc is None:
            return { "success": False, "error": "Classification code not found." }

        if description is None and type is None:
            return { "success": False, "error": "No update fields provided." }

        updated = False
        if description is not None:
            cc["description"] = description
            updated = True
        if type is not None:
            cc["type"] = type
            updated = True

        if updated:
            self.classification_codes[code] = cc
            return { "success": True, "message": "Classification code updated successfully." }
        else:
            # This branch is unreachable with the above logic, but kept for completeness.
            return { "success": False, "error": "No valid fields to update." }

    def delete_classification_code(self, code: str) -> dict:
        """
        Remove a classification code from the database. This operation is only permitted if
        the code is not currently assigned to any patent.
    
        Args:
            code (str): The classification code to remove.

        Returns:
            dict: 
                - { "success": True, "message": "Classification code <code> deleted successfully." }
                  if deletion succeeded.
                - { "success": False, "error": <reason> }
                  if code does not exist or is referenced by any patent.

        Constraints:
            - Cannot delete if the classification code is used by any patent in patents.
            - Code must exist in classification_codes.
        """
        if code not in self.classification_codes:
            return { "success": False, "error": f"Classification code '{code}' does not exist." }

        for patent in self.patents.values():
            if code in patent.get("classification_codes", []):
                return {
                    "success": False,
                    "error": f"Classification code '{code}' is assigned to at least one patent and cannot be deleted."
                }

        # Safe to delete
        del self.classification_codes[code]
        return {
            "success": True,
            "message": f"Classification code '{code}' deleted successfully."
        }

    def add_inventor(self, inventor_id: str, name: str, address: str, nationality: str) -> dict:
        """
        Add a new inventor to the Patent Database System.

        Args:
            inventor_id (str): Unique identifier for the inventor.
            name (str): Inventor's name.
            address (str): Inventor's address.
            nationality (str): Inventor's nationality.

        Returns:
            dict:
                - If success: { "success": True, "message": "Inventor added successfully." }
                - If failure: { "success": False, "error": <reason> }

        Constraints:
            - inventor_id must be unique.
            - inventor_id and name must not be empty.
        """
        if not inventor_id or not name:
            return { "success": False, "error": "inventor_id and name must not be empty." }

        if inventor_id in self.inventors:
            return { "success": False, "error": "Inventor ID already exists." }

        inventor_info: InventorInfo = {
            "inventor_id": inventor_id,
            "name": name,
            "address": address,
            "nationality": nationality
        }
        self.inventors[inventor_id] = inventor_info
        return { "success": True, "message": "Inventor added successfully." }

    def update_inventor(
        self, 
        inventor_id: str, 
        name: str = None, 
        address: str = None, 
        nationality: str = None
    ) -> dict:
        """
        Update details (name, address, nationality) for an inventor with the given inventor_id.
        Only provided (non-None) fields will be updated.

        Args:
            inventor_id (str): The unique ID of the inventor to update.
            name (str, optional): The new name for the inventor.
            address (str, optional): The new address for the inventor.
            nationality (str, optional): The new nationality for the inventor.

        Returns:
            dict: {
                "success": True,
                "message": "Inventor updated successfully.",
            }
            OR
            {
                "success": False,
                "error": str  # Error reason (e.g., inventor does not exist, no update fields provided)
            }

        Constraints:
            - Inventor with that ID must exist.
            - At least one field must be provided to update.
        """
        inventor = self.inventors.get(inventor_id)
        if inventor is None:
            return {"success": False, "error": "Inventor does not exist."}

        fields_updated = False

        if name is not None:
            inventor["name"] = name
            fields_updated = True
        if address is not None:
            inventor["address"] = address
            fields_updated = True
        if nationality is not None:
            inventor["nationality"] = nationality
            fields_updated = True

        if not fields_updated:
            return {"success": False, "error": "No update fields provided."}

        self.inventors[inventor_id] = inventor
        return {"success": True, "message": "Inventor updated successfully."}

    def delete_inventor(self, inventor_id: str) -> dict:
        """
        Delete an inventor from the patent database, only if the inventor is not referenced by any patent.

        Args:
            inventor_id (str): The ID of the inventor to delete.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Inventor deleted successfully." }
                - On error: { "success": False, "error": <reason> }

        Constraints:
            - Inventor must exist.
            - Inventor cannot be deleted if referenced by any patent's 'inventor_id'.
        """
        if inventor_id not in self.inventors:
            return { "success": False, "error": "Inventor does not exist." }

        # Check if any patent references this inventor
        referenced = any(
            patent_info["inventor_id"] == inventor_id
            for patent_info in self.patents.values()
        )
        if referenced:
            return { 
                "success": False, 
                "error": "Inventor is still referenced by one or more patents and cannot be deleted." 
            }
    
        # Safe to delete
        del self.inventors[inventor_id]
        return { "success": True, "message": "Inventor deleted successfully." }

    def validate_patent_relationships(self) -> dict:
        """
        Verify that all patent-assignee and patent-classification links are valid.
        Ensures no patent exists without at least one valid classification code,
        and that all referenced assignee_ids and classification_codes exist.

        Returns:
            dict: {
                "success": True,
                "message": "All patent relationships are valid."
            }
            or
            {
                "success": False,
                "error": str  # Description of invalid references (all found problems)
            }
        """
        errors = []

        # Validate each patent for data integrity
        for patent_id, patent in self.patents.items():
            # Check: Patents must have at least one classification code
            if not patent["classification_codes"]:
                errors.append(f"Patent '{patent_id}' has no classification codes.")
            else:
                # Check existence of each classification code
                for code in patent["classification_codes"]:
                    if code not in self.classification_codes:
                        errors.append(f"Patent '{patent_id}' references non-existent classification code '{code}'.")

            # Check existence of each assignee id
            for assignee_id in patent["assignee_ids"]:
                if assignee_id not in self.assignees:
                    errors.append(f"Patent '{patent_id}' references non-existent assignee_id '{assignee_id}'.")

        if errors:
            return {
                "success": False,
                "error": "Relationship validation failed: " + "; ".join(errors)
            }

        return {
            "success": True,
            "message": "All patent relationships are valid."
        }


class PatentDatabaseSystem(BaseEnv):
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

    def search_patents(self, **kwargs):
        return self._call_inner_tool('search_patents', kwargs)

    def get_patent_by_id(self, **kwargs):
        return self._call_inner_tool('get_patent_by_id', kwargs)

    def list_patent_titles(self, **kwargs):
        return self._call_inner_tool('list_patent_titles', kwargs)

    def get_patent_assignee_ids(self, **kwargs):
        return self._call_inner_tool('get_patent_assignee_ids', kwargs)

    def get_assignee_by_id(self, **kwargs):
        return self._call_inner_tool('get_assignee_by_id', kwargs)

    def get_assignee_name_by_id(self, **kwargs):
        return self._call_inner_tool('get_assignee_name_by_id', kwargs)

    def list_patents_by_classification_code(self, **kwargs):
        return self._call_inner_tool('list_patents_by_classification_code', kwargs)

    def list_classification_codes(self, **kwargs):
        return self._call_inner_tool('list_classification_codes', kwargs)

    def get_patent_classification_codes(self, **kwargs):
        return self._call_inner_tool('get_patent_classification_codes', kwargs)

    def list_patents_by_assignee_id(self, **kwargs):
        return self._call_inner_tool('list_patents_by_assignee_id', kwargs)

    def list_assignees(self, **kwargs):
        return self._call_inner_tool('list_assignees', kwargs)

    def list_inventors(self, **kwargs):
        return self._call_inner_tool('list_inventors', kwargs)

    def get_inventor_by_id(self, **kwargs):
        return self._call_inner_tool('get_inventor_by_id', kwargs)

    def add_patent(self, **kwargs):
        return self._call_inner_tool('add_patent', kwargs)

    def update_patent(self, **kwargs):
        return self._call_inner_tool('update_patent', kwargs)

    def delete_patent(self, **kwargs):
        return self._call_inner_tool('delete_patent', kwargs)

    def add_assignee(self, **kwargs):
        return self._call_inner_tool('add_assignee', kwargs)

    def update_assignee(self, **kwargs):
        return self._call_inner_tool('update_assignee', kwargs)

    def delete_assignee(self, **kwargs):
        return self._call_inner_tool('delete_assignee', kwargs)

    def add_classification_code(self, **kwargs):
        return self._call_inner_tool('add_classification_code', kwargs)

    def update_classification_code(self, **kwargs):
        return self._call_inner_tool('update_classification_code', kwargs)

    def delete_classification_code(self, **kwargs):
        return self._call_inner_tool('delete_classification_code', kwargs)

    def add_inventor(self, **kwargs):
        return self._call_inner_tool('add_inventor', kwargs)

    def update_inventor(self, **kwargs):
        return self._call_inner_tool('update_inventor', kwargs)

    def delete_inventor(self, **kwargs):
        return self._call_inner_tool('delete_inventor', kwargs)

    def validate_patent_relationships(self, **kwargs):
        return self._call_inner_tool('validate_patent_relationships', kwargs)
