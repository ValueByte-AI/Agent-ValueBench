# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
from datetime import datetime



class DatasetInfo(TypedDict):
    dataset_id: str
    title: str
    description: str
    source_agency_id: str
    update_date: str
    data_format: str
    availability_status: str
    creation_date: str
    keywords: List[str]

class AgencyInfo(TypedDict):
    agency_id: str
    name: str
    contact_info: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment modeling a government open data portal API.
        """
        # Datasets: {dataset_id: DatasetInfo}
        self.datasets: Dict[str, DatasetInfo] = {}

        # Agencies: {agency_id: AgencyInfo}
        self.agencies: Dict[str, AgencyInfo] = {}

        # Constraints:
        # - Each dataset must have a unique dataset_id.
        # - Each dataset must reference a valid source_agency.
        # - Only datasets with availability_status = "published" are accessible via the API.
        # - Metadata fields (e.g., description, update_date) must be kept in sync with actual published data.

    def get_dataset_metadata(self, dataset_id: str) -> dict:
        """
        Retrieve complete metadata for a single dataset by its unique dataset_id,
        only if its availability_status is "published".

        Args:
            dataset_id (str): The unique identifier of the dataset.

        Returns:
            dict: {
                "success": True,
                "data": DatasetInfo
            }
            or
            {
                "success": False,
                "error": str  # Error message
            }

        Constraints:
            - Only return datasets with availability_status == "published".
            - Return error if dataset_id does not exist.
        """
        dataset = self.datasets.get(dataset_id)
        if not dataset:
            return { "success": False, "error": "Dataset does not exist" }
        if dataset["availability_status"] != "published":
            return { "success": False, "error": "Dataset is not published" }
        return { "success": True, "data": dataset }

    def search_datasets_by_title(self, substring: str) -> dict:
        """
        Search for datasets whose titles contain the specified substring (case-insensitive),
        returning only those with availability_status == "published".

        Args:
            substring (str): Substring to match within dataset titles.

        Returns:
            dict: {
                "success": True,
                "data": List[DatasetInfo],  # List of datasets matching criteria, may be empty
            }

        Constraints:
            - Only datasets with availability_status = "published" are included in the result.
            - String match is case-insensitive.
        """
        lower_substring = substring.lower()
        result = [
            dataset_info
            for dataset_info in self.datasets.values()
            if (
                dataset_info["availability_status"] == "published"
                and lower_substring in dataset_info["title"].lower()
            )
        ]
        return { "success": True, "data": result }

    def search_datasets_by_keyword(self, keyword: str) -> dict:
        """
        Retrieve all published datasets that are tagged with the specified keyword.

        Args:
            keyword (str): The keyword/tag to search for (case-insensitive).

        Returns:
            dict:
                - success (bool): True if query is processed.
                - data (List[DatasetInfo]): List of published datasets containing the keyword.
                - error (str, optional): If invalid input.

        Constraints:
            - Only datasets with availability_status == "published" are considered.
            - Keyword search is case-insensitive.
            - Keyword must be a non-empty string.
        """
        if not isinstance(keyword, str) or not keyword.strip():
            return { "success": False, "error": "Keyword must be a non-empty string" }

        keyword_lower = keyword.strip().lower()
        result = [
            dataset for dataset in self.datasets.values()
            if dataset.get("availability_status") == "published"
            and any(k.lower() == keyword_lower for k in dataset.get("keywords", []))
        ]
        return { "success": True, "data": result }

    def list_datasets_by_agency(self, source_agency_id: str) -> dict:
        """
        List all published datasets from a specified source_agency_id.

        Args:
            source_agency_id (str): The ID of the agency whose published datasets to list.

        Returns:
            dict: {
                "success": True,
                "data": List[DatasetInfo]  # List of published datasets for this agency (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Description (e.g., agency not found)
            }

        Constraints:
            - Agency must exist.
            - Only datasets with availability_status == "published" are returned.
        """
        if source_agency_id not in self.agencies:
            return { "success": False, "error": "Agency does not exist" }
    
        result = [
            dataset for dataset in self.datasets.values()
            if dataset["source_agency_id"] == source_agency_id and dataset["availability_status"] == "published"
        ]
    
        return { "success": True, "data": result }

    def get_agency_info(self, agency_id: str) -> dict:
        """
        Retrieve agency information (name and contact) based on agency_id.

        Args:
            agency_id (str): The unique identifier for the government agency.

        Returns:
            dict: 
                {"success": True, "data": AgencyInfo} on success,
                {"success": False, "error": "Agency not found"} if agency_id is invalid.

        Constraints:
            - agency_id must exist in the system.
        """
        agency = self.agencies.get(agency_id)
        if not agency:
            return { "success": False, "error": "Agency not found" }
        return { "success": True, "data": agency }

    def list_all_agencies(self) -> dict:
        """
        Retrieve a list of all agencies registered within the portal.

        Returns:
            dict: {
                "success": True,
                "data": List[AgencyInfo],  # List of all agencies (can be empty if none registered)
            }
        Constraints:
            - None. Always returns (empty list if no agencies).
        """
        agencies_list = list(self.agencies.values())
        return {
            "success": True,
            "data": agencies_list
        }

    def list_all_published_datasets(self) -> dict:
        """
        Retrieve a list of all datasets where availability_status == "published".

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[DatasetInfo],  # List may be empty if there are no published datasets
            }
        """
        result = [
            dataset_info
            for dataset_info in self.datasets.values()
            if dataset_info.get("availability_status") == "published"
        ]
        return { "success": True, "data": result }

    def check_dataset_exists(self, dataset_id: str) -> dict:
        """
        Check whether a dataset with the given dataset_id exists in the portal.

        Args:
            dataset_id (str): The unique identifier of the dataset.

        Returns:
            dict: {
                "success": True,
                "data": bool  # True if exists, False otherwise.
            }
            If dataset_id is invalid (None or empty), returns False for existence.

        Constraints:
            - None directly; simply checks presence in datasets dict.
        """
        if not dataset_id or not isinstance(dataset_id, str):
            return { "success": True, "data": False }
        exists = dataset_id in self.datasets
        return { "success": True, "data": exists }

    def get_dataset_update_date(self, dataset_id: str) -> dict:
        """
        Retrieve the last update date for a given dataset, if it exists and is published.

        Args:
            dataset_id (str): Unique identifier of the dataset.

        Returns:
            dict: {
                "success": True,
                "data": str  # The update_date of the dataset (format as stored)
            }
            or
            {
                "success": False,
                "error": str  # Error message, e.g., dataset does not exist or not published
            }

        Constraints:
            - Dataset must exist in the portal.
            - Dataset must have availability_status == "published".
        """
        dataset = self.datasets.get(dataset_id)
        if dataset is None:
            return {"success": False, "error": "Dataset does not exist"}
    
        if dataset.get("availability_status") != "published":
            return {"success": False, "error": "Dataset is not published and cannot be accessed"}
    
        return {"success": True, "data": dataset.get("update_date")}

    def publish_dataset(self, dataset_id: str) -> dict:
        """
        Sets a dataset's availability_status to 'published' if:
        - The dataset exists.
        - The dataset references a valid agency.
        - The dataset's metadata is considered 'synced' (basic check: required fields are non-empty).
    
        Args:
            dataset_id (str): The dataset's unique identifier.
    
        Returns:
            dict: 
                On success: { "success": True, "message": "Dataset <dataset_id> published successfully." }
                On failure: { "success": False, "error": "<reason>" }
        """
        # Check dataset existence
        dataset = self.datasets.get(dataset_id)
        if dataset is None:
            return { "success": False, "error": f"Dataset '{dataset_id}' does not exist." }

        # Check agency reference validity
        agency_id = dataset.get("source_agency_id")
        if not agency_id or agency_id not in self.agencies:
            return { "success": False, "error": "Dataset references an invalid or missing agency." }

        # Metadata sync check (minimal: required fields are non-empty)
        required_fields = [
            'title', 'description', 'update_date', 'data_format', 'availability_status',
            'creation_date', 'keywords'
        ]
        for field in required_fields:
            val = dataset.get(field)
            # For string fields, must be non-empty; for keywords (list), must be non-empty list
            if (isinstance(val, str) and not val.strip()) or (isinstance(val, list) and not val):
                return { "success": False, "error": f"Metadata field '{field}' is missing or empty." }

        # Set as 'published'
        dataset['availability_status'] = "published"
        # (Assuming meta update_date is not auto-changed here)

        return {
            "success": True,
            "message": f"Dataset '{dataset_id}' published successfully."
        }

    def unpublish_dataset(self, dataset_id: str) -> dict:
        """
        Set a dataset's availability_status to "unpublished," making it inaccessible via the API.

        Args:
            dataset_id (str): The unique identifier of the dataset to unpublish.

        Returns:
            dict: 
                - { "success": True, "message": "Dataset <dataset_id> unpublished." }
                - { "success": False, "error": "Dataset does not exist." }

        Constraints:
            - The dataset must exist in self.datasets.
            - After this operation, dataset is excluded from published-dataset queries.
        """
        if dataset_id not in self.datasets:
            return { "success": False, "error": "Dataset does not exist." }
    
        self.datasets[dataset_id]["availability_status"] = "unpublished"
        return { "success": True, "message": f"Dataset {dataset_id} unpublished." }

    def sync_dataset_metadata(self, dataset_id: str) -> dict:
        """
        Ensure that the metadata fields of the given published dataset are up-to-date and consistent with the published source.

        Args:
            dataset_id (str): The identifier of the dataset to synchronize.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Dataset metadata synchronized for <dataset_id>"
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason for failure
                    }

        Constraints:
            - Dataset must exist.
            - Dataset must reference a valid source agency.
            - Only published datasets are allowed.
            - The "sync" operation is simulated; metadata fields are "refreshed" and update_date updated.
        """

        if dataset_id not in self.datasets:
            return { "success": False, "error": "Dataset does not exist" }

        dataset = self.datasets[dataset_id]

        if dataset["availability_status"] != "published":
            return { "success": False, "error": "Only published datasets can be synchronized" }

        agency_id = dataset["source_agency_id"]
        if agency_id not in self.agencies:
            return { "success": False, "error": "Dataset references an invalid source agency" }

        # Simulate sync: refresh metadata and update 'update_date' to current ISO date string.
        now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        # For simulation, just update the update_date.
        dataset["update_date"] = now
        self.datasets[dataset_id] = dataset  # Persist update (if dict is not a reference)

        return {
            "success": True,
            "message": f"Dataset metadata synchronized for {dataset_id}"
        }

    def add_dataset(self, dataset_info: dict) -> dict:
        """
        Add a new dataset to the portal.

        Args:
            dataset_info (dict): Must contain all required fields for DatasetInfo:
                - dataset_id (str)
                - title (str)
                - description (str)
                - source_agency_id (str)  # Must exist in self.agencies
                - update_date (str)
                - data_format (str)
                - availability_status (str)
                - creation_date (str)
                - keywords (List[str])

        Returns:
            dict: {
                "success": True,
                "message": "Dataset <dataset_id> added successfully"
            }
            or
            {
                "success": False,
                "error": str  # explanation
            }

        Constraints:
            - dataset_id must be unique.
            - source_agency_id must refer to a present agency.
        """
        # Minimal field presence check
        required_fields = [
            "dataset_id", "title", "description", "source_agency_id",
            "update_date", "data_format", "availability_status", "creation_date", "keywords"
        ]
        for field in required_fields:
            if field not in dataset_info:
                return {"success": False, "error": f"Missing field: {field}"}

        dataset_id = dataset_info["dataset_id"]
        source_agency_id = dataset_info["source_agency_id"]

        if dataset_id in self.datasets:
            return { "success": False, "error": "Dataset ID already exists" }

        if source_agency_id not in self.agencies:
            return { "success": False, "error": "Source agency does not exist" }

        # Insert
        self.datasets[dataset_id] = {
            "dataset_id": dataset_info["dataset_id"],
            "title": dataset_info["title"],
            "description": dataset_info["description"],
            "source_agency_id": dataset_info["source_agency_id"],
            "update_date": dataset_info["update_date"],
            "data_format": dataset_info["data_format"],
            "availability_status": dataset_info["availability_status"],
            "creation_date": dataset_info["creation_date"],
            "keywords": dataset_info["keywords"],
        }

        return { "success": True, "message": f"Dataset {dataset_id} added successfully" }

    def update_dataset_metadata(self, dataset_id: str, updates: dict) -> dict:
        """
        Modify metadata fields of an existing dataset.

        Args:
            dataset_id (str): ID of the dataset to update.
            updates (dict): Dict of field: new_value pairs to update. 
                - Allowed fields: any from DatasetInfo except 'dataset_id'.

        Returns:
            dict: {
                "success": True,
                "message": "Dataset metadata updated for <dataset_id>"
            }
            OR
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Dataset must exist.
            - Only valid metadata fields (from DatasetInfo except 'dataset_id') are allowed.
            - If updating 'source_agency_id', must refer to an existing agency.
            - 'dataset_id' cannot be changed.
        """
        if dataset_id not in self.datasets:
            return { "success": False, "error": "Dataset does not exist" }

        # Construct set of allowed fields (all except 'dataset_id')
        allowed_fields = set(self.datasets[dataset_id].keys()) - {"dataset_id"}

        for field, value in updates.items():
            if field not in allowed_fields:
                return { "success": False, "error": f"Field '{field}' update is not allowed" }
            if field == "source_agency_id":
                if value not in self.agencies:
                    return { "success": False, "error": "Referenced agency does not exist" }
            # Optional: add further validations here (such as allowed values for availability_status)

        # All validations passed, perform the updates
        for field, value in updates.items():
            self.datasets[dataset_id][field] = value

        return { "success": True, "message": f"Dataset metadata updated for {dataset_id}" }

    def delete_dataset(self, dataset_id: str) -> dict:
        """
        Remove a dataset from the portal by its unique dataset_id.

        Args:
            dataset_id (str): The identifier of the dataset to delete.

        Returns:
            dict:
                - success (bool): True if deletion succeeded, False otherwise.
                - message (str): Operation description if successful.
                - error (str): Error reason if not successful.

        Constraints:
            - The dataset identified by dataset_id must exist.
        """
        if dataset_id not in self.datasets:
            return {
                "success": False,
                "error": f"Dataset with id '{dataset_id}' does not exist."
            }
        del self.datasets[dataset_id]
        return {
            "success": True,
            "message": f"Dataset '{dataset_id}' has been deleted."
        }

    def add_agency(self, agency_id: str, name: str, contact_info: str) -> dict:
        """
        Add a new agency entry into the portal's agency list.

        Args:
            agency_id (str): Unique identifier for the agency.
            name (str): Human-readable agency name.
            contact_info (str): Contact information for the agency.

        Returns:
            dict: Success or failure message.
                On success:
                    {
                        "success": True,
                        "message": "Agency <agency_id> added successfully"
                    }
                On failure:
                    {
                        "success": False,
                        "error": <reason>
                    }

        Constraints:
            - agency_id must not already exist in self.agencies.
        """
        if agency_id in self.agencies:
            return {
                "success": False,
                "error": f"Agency with agency_id '{agency_id}' already exists"
            }

        self.agencies[agency_id] = {
            "agency_id": agency_id,
            "name": name,
            "contact_info": contact_info
        }
        return {
            "success": True,
            "message": f"Agency {agency_id} added successfully"
        }

    def update_agency_info(
        self,
        agency_id: str,
        name: str = None,
        contact_info: str = None
    ) -> dict:
        """
        Edit the name and/or contact information for an existing agency.

        Args:
            agency_id (str): The ID of the agency to update.
            name (str, optional): The new agency name (if updating).
            contact_info (str, optional): The new contact information (if updating).

        Returns:
            dict: {
                "success": True,
                "message": "Agency information updated successfully"
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - The agency_id must exist in the environment.
            - At least one of `name` or `contact_info` must be provided for update.
        """
        if agency_id not in self.agencies:
            return { "success": False, "error": "Agency does not exist" }
        if name is None and contact_info is None:
            return { "success": False, "error": "No updates specified (name or contact_info required)" }
        if name is not None:
            self.agencies[agency_id]['name'] = name
        if contact_info is not None:
            self.agencies[agency_id]['contact_info'] = contact_info
        return { "success": True, "message": "Agency information updated successfully" }


class OpenDataPortalAPI(BaseEnv):
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

    def get_dataset_metadata(self, **kwargs):
        return self._call_inner_tool('get_dataset_metadata', kwargs)

    def search_datasets_by_title(self, **kwargs):
        return self._call_inner_tool('search_datasets_by_title', kwargs)

    def search_datasets_by_keyword(self, **kwargs):
        return self._call_inner_tool('search_datasets_by_keyword', kwargs)

    def list_datasets_by_agency(self, **kwargs):
        return self._call_inner_tool('list_datasets_by_agency', kwargs)

    def get_agency_info(self, **kwargs):
        return self._call_inner_tool('get_agency_info', kwargs)

    def list_all_agencies(self, **kwargs):
        return self._call_inner_tool('list_all_agencies', kwargs)

    def list_all_published_datasets(self, **kwargs):
        return self._call_inner_tool('list_all_published_datasets', kwargs)

    def check_dataset_exists(self, **kwargs):
        return self._call_inner_tool('check_dataset_exists', kwargs)

    def get_dataset_update_date(self, **kwargs):
        return self._call_inner_tool('get_dataset_update_date', kwargs)

    def publish_dataset(self, **kwargs):
        return self._call_inner_tool('publish_dataset', kwargs)

    def unpublish_dataset(self, **kwargs):
        return self._call_inner_tool('unpublish_dataset', kwargs)

    def sync_dataset_metadata(self, **kwargs):
        return self._call_inner_tool('sync_dataset_metadata', kwargs)

    def add_dataset(self, **kwargs):
        return self._call_inner_tool('add_dataset', kwargs)

    def update_dataset_metadata(self, **kwargs):
        return self._call_inner_tool('update_dataset_metadata', kwargs)

    def delete_dataset(self, **kwargs):
        return self._call_inner_tool('delete_dataset', kwargs)

    def add_agency(self, **kwargs):
        return self._call_inner_tool('add_agency', kwargs)

    def update_agency_info(self, **kwargs):
        return self._call_inner_tool('update_agency_info', kwargs)

