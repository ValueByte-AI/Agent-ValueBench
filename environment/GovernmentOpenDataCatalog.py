# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
from typing import Optional, List
from datetime import datetime



class PublisherInfo(TypedDict):
    publisher_id: str
    name: str
    description: str
    country: str
    contact_info: str

class TopicInfo(TypedDict):
    topic_id: str
    name: str
    description: str

class FormatInfo(TypedDict):
    format_id: str
    name: str
    description: str
    mime_type: str

class AccessMethodInfo(TypedDict):
    access_method_id: str
    type: str
    url: str
    authentication_required: bool

class DatasetInfo(TypedDict):
    dataset_id: str
    title: str
    description: str
    publisher_id: str
    topic: List[str]  # List of topic_ids
    format: str       # format_id
    access_methods: List[str]  # List of access_method_ids
    release_date: str
    update_frequency: str
    license: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Publishers: {publisher_id: PublisherInfo}
        self.publishers: Dict[str, PublisherInfo] = {}
        # Datasets: {dataset_id: DatasetInfo}
        self.datasets: Dict[str, DatasetInfo] = {}
        # Topics: {topic_id: TopicInfo}
        self.topics: Dict[str, TopicInfo] = {}
        # Formats: {format_id: FormatInfo}
        self.formats: Dict[str, FormatInfo] = {}
        # Access Methods: {access_method_id: AccessMethodInfo}
        self.access_methods: Dict[str, AccessMethodInfo] = {}

        # Constraints:
        # - Each dataset must be associated with exactly one publisher.
        # - Datasets may be categorized under one or more topics.
        # - Each dataset must specify at least one access method.
        # - Dataset formats must be chosen from a predefined list of formats.

    def list_publishers(self) -> dict:
        """
        Retrieve the list of all publishers in the catalog.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[PublisherInfo]  # List of all PublisherInfo objects (can be empty)
            }
        """
        return {
            "success": True,
            "data": list(self.publishers.values())
        }

    def get_publisher_by_id(self, publisher_id: str) -> dict:
        """
        Retrieve detailed metadata about a specific publisher by its publisher_id.

        Args:
            publisher_id (str): Unique identifier for the publisher.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": PublisherInfo
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Publisher not found"
                    }

        Constraints:
            - publisher_id must exist in the catalog.
        """
        if publisher_id not in self.publishers:
            return {"success": False, "error": "Publisher not found"}
        return {"success": True, "data": self.publishers[publisher_id]}

    def list_publishers_by_country(self, country: str) -> dict:
        """
        List all publishers filtered by a specific country.

        Args:
            country (str): The country to filter publishers by.

        Returns:
            dict: {
                "success": True,
                "data": List[PublisherInfo]  # List of publishers from the given country (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - 'country' must be a non-empty string.
        """
        if not isinstance(country, str) or not country.strip():
            return { "success": False, "error": "Country parameter must be a non-empty string" }

        result = [
            publisher for publisher in self.publishers.values()
            if publisher["country"] == country
        ]
        return { "success": True, "data": result }

    def get_dataset_by_id(self, dataset_id: str) -> dict:
        """
        Retrieve detailed metadata about a specific dataset by its dataset_id.

        Args:
            dataset_id (str): The unique identifier of the dataset.

        Returns:
            dict:
                - On success: {"success": True, "data": DatasetInfo}
                - On failure: {"success": False, "error": "Dataset not found"}

        Constraints:
            - Only retrieves info; does not enforce constraints on access or modification.
        """
        dataset = self.datasets.get(dataset_id)
        if not dataset:
            return {"success": False, "error": "Dataset not found"}
        return {"success": True, "data": dataset}

    def list_datasets(self) -> dict:
        """
        Get a list of all datasets in the catalog.

        Returns:
            dict: {
                "success": True,
                "data": List[DatasetInfo]  # All dataset metadata (may be empty)
            }
        """
        all_datasets = list(self.datasets.values())
        return {
            "success": True,
            "data": all_datasets
        }

    def list_datasets_by_publisher(self, publisher_id: str) -> dict:
        """
        Retrieve all datasets associated with a specified publisher_id.

        Args:
            publisher_id (str): The ID of the publisher.

        Returns:
            dict: {
                "success": True,
                "data": List[DatasetInfo]  # list may be empty if publisher has no datasets
            }
            OR
            {
                "success": False,
                "error": str  # If publisher_id is not found
            }

        Constraints:
            - The publisher_id must exist in the catalog.
        """
        if publisher_id not in self.publishers:
            return { "success": False, "error": "Publisher not found" }

        results = [
            dataset_info
            for dataset_info in self.datasets.values()
            if dataset_info["publisher_id"] == publisher_id
        ]
        return { "success": True, "data": results }

    def list_datasets_by_topic(self, topic_id: str) -> dict:
        """
        Retrieve all datasets categorized under the specified topic_id.

        Args:
            topic_id (str): Unique identifier of the topic.

        Returns:
            dict: {
                "success": True,
                "data": List[DatasetInfo],  # List is empty if no datasets found
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g. topic does not exist
            }

        Constraints:
            - The topic_id must exist in the system.
        """
        if topic_id not in self.topics:
            return {"success": False, "error": "Topic does not exist"}

        result = [
            dataset for dataset in self.datasets.values()
            if topic_id in dataset.get("topic", [])
        ]

        return {"success": True, "data": result}

    def list_datasets_by_format(self, format_id: str) -> dict:
        """
        Retrieve all datasets using the specified format ID.

        Args:
            format_id (str): The ID of the format to filter datasets.

        Returns:
            dict: 
              - {"success": True, "data": List[DatasetInfo]} if format_id exists (may be empty list).
              - {"success": False, "error": str} if the format_id does not exist.

        Constraints:
            - format_id must exist in self.formats (formats must be predefined).
            - Only datasets whose 'format' matches format_id are included.
        """
        if format_id not in self.formats:
            return {"success": False, "error": "Format not found"}

        result = [
            dataset for dataset in self.datasets.values()
            if dataset["format"] == format_id
        ]

        return {"success": True, "data": result}

    def list_datasets_by_access_method(self, access_method_id: str) -> dict:
        """
        Retrieve all datasets that include the specified access_method_id in their access_methods.

        Args:
            access_method_id (str): The ID of the access method to filter datasets by.

        Returns:
            dict: {
                "success": True,
                "data": List[DatasetInfo],  # List of datasets using this access method (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Description if the access method does not exist
            }

        Constraints:
            - The access_method_id must exist in the catalog.
        """
        if access_method_id not in self.access_methods:
            return { "success": False, "error": "Access method does not exist" }

        matching_datasets = [
            dataset_info
            for dataset_info in self.datasets.values()
            if access_method_id in dataset_info["access_methods"]
        ]

        return { "success": True, "data": matching_datasets }

    def list_topics(self) -> dict:
        """
        Retrieves a list of all available topics in the open data catalog.

        Returns:
            dict: {
                "success": True,
                "data": List[TopicInfo],  # List of all topic information (may be empty)
            }

        Notes:
            - No input parameters required.
            - No constraints or permission checks for this operation.
        """
        topics_list = list(self.topics.values())
        return {
            "success": True,
            "data": topics_list
        }

    def get_topic_by_id(self, topic_id: str) -> dict:
        """
        Retrieve detailed information about a topic by its topic_id.

        Args:
            topic_id (str): The unique identifier of the topic.

        Returns:
            dict: 
                { "success": True, "data": TopicInfo } if the topic is found,
                { "success": False, "error": "Topic not found" } otherwise.
        """
        topic_info = self.topics.get(topic_id)
        if topic_info is not None:
            return { "success": True, "data": topic_info }
        else:
            return { "success": False, "error": "Topic not found" }

    def list_formats(self) -> dict:
        """
        Retrieve a list of all available data formats in the open data catalog.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[FormatInfo]  # List of format metadata (may be empty if no formats present)
            }
        """
        data = list(self.formats.values())
        return { "success": True, "data": data }

    def get_format_by_id(self, format_id: str) -> dict:
        """
        Retrieve detailed information about a format by its format_id.

        Args:
            format_id (str): The unique identifier of the data format.

        Returns:
            dict: {
                "success": True,
                "data": FormatInfo  # The detailed format information
            }
            OR
            {
                "success": False,
                "error": str  # Error message if format_id is not present
            }

        Constraints:
            - format_id must exist in the catalog's self.formats dictionary.
        """
        if format_id not in self.formats:
            return { "success": False, "error": "Format not found" }
        return { "success": True, "data": self.formats[format_id] }

    def list_access_methods(self) -> dict:
        """
        Get a list of all available access methods.

        Returns:
            dict:
                success (bool): True if listing possible.
                data (List[AccessMethodInfo]): List of all access method info (may be empty).
        """
        return {
            "success": True,
            "data": list(self.access_methods.values())
        }

    def get_access_method_by_id(self, access_method_id: str) -> dict:
        """
        Retrieve detailed information about a specific access method.

        Args:
            access_method_id (str): The unique identifier of the access method.

        Returns:
            dict: 
                If found: {
                    "success": True,
                    "data": AccessMethodInfo
                }
                If not found: {
                    "success": False,
                    "error": "Access method with ID '<id>' not found"
                }
        """
        if access_method_id not in self.access_methods:
            return {
                "success": False,
                "error": f"Access method with ID '{access_method_id}' not found"
            }
        return {
            "success": True,
            "data": self.access_methods[access_method_id]
        }


    def list_datasets_by_release_date(
        self, 
        release_date: Optional[str] = None, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> dict:
        """
        Retrieve datasets filtered by release_date (exact match) or within an inclusive date range.

        Args:
            release_date (Optional[str]): Filter for datasets released exactly on this date (YYYY-MM-DD).
            start_date (Optional[str]): Start of release date range (inclusive, YYYY-MM-DD).
            end_date (Optional[str]): End of release date range (inclusive, YYYY-MM-DD).

        Returns:
            dict: {
                "success": True,
                "data": List[DatasetInfo]
            } on success, or
            {
                "success": False,
                "error": str
            } on error.

        Constraints:
            - If both range and exact release_date are provided, the range takes precedence.
            - If no filters are specified, returns error.
            - Dates must be in YYYY-MM-DD format.
        """

        # Helper to validate date string
        def _is_valid_date(date_str: str) -> bool:
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
                return True
            except Exception:
                return False

        # At least one filter must be specified
        if not release_date and not (start_date and end_date):
            return {"success": False, "error": "At least one filter (release_date or date range) must be specified"}

        # Range takes precedence if provided
        if start_date and end_date:
            if not (_is_valid_date(start_date) and _is_valid_date(end_date)):
                return {"success": False, "error": "Date range values must be in YYYY-MM-DD format"}
            try:
                d_start = datetime.strptime(start_date, "%Y-%m-%d")
                d_end = datetime.strptime(end_date, "%Y-%m-%d")
            except Exception:
                return {"success": False, "error": "Invalid date range format"}
            if d_start > d_end:
                return {"success": False, "error": "start_date cannot be after end_date"}
            # Filter datasets within range (inclusive)
            data = [
                ds
                for ds in self.datasets.values()
                if _is_valid_date(ds["release_date"]) and d_start <= datetime.strptime(ds["release_date"], "%Y-%m-%d") <= d_end
            ]
            return {"success": True, "data": data}

        # Otherwise, use release_date filter
        if release_date:
            if not _is_valid_date(release_date):
                return {"success": False, "error": "release_date must be in YYYY-MM-DD format"}
            data = [
                ds for ds in self.datasets.values()
                if ds["release_date"] == release_date
            ]
            return {"success": True, "data": data}

        # Defensive fallback (should never reach here)
        return {"success": False, "error": "Invalid parameters"}

    def list_datasets_by_update_frequency(self, update_frequency: str) -> dict:
        """
        Retrieve all datasets that match the given update_frequency.

        Args:
            update_frequency (str): The update frequency value to match (e.g., "monthly").

        Returns:
            dict: {
                "success": True,
                "data": List[DatasetInfo]  # List (possibly empty) of matching datasets
            }
            or
            {
                "success": False,
                "error": str  # Description of input error
            }

        Constraints:
            - `update_frequency` must be a non-empty string.
        """
        if not update_frequency or not isinstance(update_frequency, str):
            return {"success": False, "error": "Invalid or missing update_frequency parameter"}

        matching = [
            dataset for dataset in self.datasets.values()
            if dataset["update_frequency"] == update_frequency
        ]

        return {"success": True, "data": matching}

    def list_datasets_by_license(self, license: str) -> dict:
        """
        Retrieve all datasets with the specified license.

        Args:
            license (str): The license string to filter datasets.

        Returns:
            dict:
                - success (bool): Always True if operation completes.
                - data (List[DatasetInfo]): List of dataset metadata where 'license' matches query.

        Notes:
            - The match is exact (case-sensitive).
            - Returns an empty list if no matching datasets are found.
        """
        matching = [
            dataset_info
            for dataset_info in self.datasets.values()
            if dataset_info.get("license") == license
        ]
        return { "success": True, "data": matching }

    def add_publisher(
        self,
        publisher_id: str,
        name: str,
        description: str,
        country: str,
        contact_info: str
    ) -> dict:
        """
        Add a new publisher to the catalog.

        Args:
            publisher_id (str): Unique identifier for the publisher.
            name (str): Name of the publisher.
            description (str): Description of the publisher.
            country (str): Country of the publisher.
            contact_info (str): Contact information of the publisher.

        Returns:
            dict: {
                "success": True,
                "message": "Publisher added successfully"
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - publisher_id must be unique (not already in catalog)
            - All fields required and non-empty
        """
        if not publisher_id:
            return { "success": False, "error": "Missing required field: publisher_id" }
        if not name:
            return { "success": False, "error": "Missing required field: name" }
        if not description:
            return { "success": False, "error": "Missing required field: description" }
        if not country:
            return { "success": False, "error": "Missing required field: country" }
        if not contact_info:
            return { "success": False, "error": "Missing required field: contact_info" }

        if publisher_id in self.publishers:
            return { "success": False, "error": "Publisher ID already exists" }

        self.publishers[publisher_id] = {
            "publisher_id": publisher_id,
            "name": name,
            "description": description,
            "country": country,
            "contact_info": contact_info,
        }

        return { "success": True, "message": "Publisher added successfully" }

    def update_publisher(
        self, 
        publisher_id: str, 
        name: str = None, 
        description: str = None, 
        country: str = None, 
        contact_info: str = None
    ) -> dict:
        """
        Update metadata fields (name, description, country, contact_info) of an existing publisher.

        Args:
            publisher_id (str): Identifier for the publisher to update.
            name (str, optional): New name.
            description (str, optional): New description.
            country (str, optional): New country value.
            contact_info (str, optional): New contact info.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Publisher updated successfully" }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - Publisher must already exist.
            - At least one updatable field must be provided.
            - publisher_id is not updatable.
        """
        if publisher_id not in self.publishers:
            return { "success": False, "error": "Publisher not found" }

        update_fields = {}
        if name is not None:
            update_fields['name'] = name
        if description is not None:
            update_fields['description'] = description
        if country is not None:
            update_fields['country'] = country
        if contact_info is not None:
            update_fields['contact_info'] = contact_info

        if not update_fields:
            return { "success": False, "error": "No update fields provided" }

        # Perform update
        self.publishers[publisher_id].update(update_fields)

        return { "success": True, "message": "Publisher updated successfully" }

    def remove_publisher(self, publisher_id: str) -> dict:
        """
        Remove a publisher from the catalog if no datasets reference it.

        Args:
            publisher_id (str): The ID of the publisher to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Publisher <publisher_id> removed from catalog"
            }
            OR
            {
                "success": False,
                "error": "reason why removal failed"
            }

        Constraints:
            - Publisher must exist in the catalog.
            - Publisher must not be referenced by any existing dataset.
        """
        if publisher_id not in self.publishers:
            return {"success": False, "error": "Publisher does not exist"}

        # Check if any dataset references this publisher
        for dataset in self.datasets.values():
            if dataset["publisher_id"] == publisher_id:
                return {
                    "success": False, 
                    "error": "Publisher cannot be removed: referenced by at least one dataset"
                }

        # If not referenced, delete
        del self.publishers[publisher_id]
        return {
            "success": True,
            "message": f"Publisher {publisher_id} removed from catalog"
        }

    def add_dataset(
        self, 
        dataset_id: str,
        title: str,
        description: str,
        publisher_id: str,
        topic: List[str],
        format: str,
        access_methods: List[str],
        release_date: str,
        update_frequency: str,
        license: str
    ) -> dict:
        """
        Add a new dataset entry to the catalog, enforcing all relevant constraints.
    
        Args:
            dataset_id (str): Unique identifier for the dataset.
            title (str): Title of the dataset.
            description (str): Description of the dataset.
            publisher_id (str): The publisher's unique identifier.
            topic (List[str]): List of topic_ids; each must exist in catalog (can be empty).
            format (str): format_id; must exist in catalog.
            access_methods (List[str]): List of access_method_ids; at least one, all must exist.
            release_date (str): Dataset's original release date.
            update_frequency (str): Frequency of updates.
            license (str): License string.
    
        Returns:
            dict: {
                "success": True,
                "message": "Dataset <dataset_id> added."
            } 
            OR
            {
                "success": False,
                "error": "<reason>"
            }
    
        Constraints:
            - dataset_id must be unique.
            - publisher_id must exist.
            - format must exist.
            - At least one valid access_method_id must be supplied and exist.
            - If topic is non-empty, all topic_ids must exist.
        """
        # Check for unique dataset_id
        if dataset_id in self.datasets:
            return { "success": False, "error": "Dataset ID already exists." }
    
        # Check for publisher existence
        if publisher_id not in self.publishers:
            return { "success": False, "error": "Publisher does not exist." }
    
        # Check for format existence
        if format not in self.formats:
            return { "success": False, "error": "Format does not exist." }
    
        # At least one access method, all must exist
        if not isinstance(access_methods, list) or len(access_methods) == 0:
            return { "success": False, "error": "At least one access method must be specified." }
        for aid in access_methods:
            if aid not in self.access_methods:
                return { "success": False, "error": f"Access method '{aid}' does not exist." }
    
        # If there are topics, ensure all exist
        if not isinstance(topic, list):
            return { "success": False, "error": "Topics must be a list." }
        for tid in topic:
            if tid not in self.topics:
                return { "success": False, "error": f"Topic '{tid}' does not exist." }
    
        # All good: add dataset
        dataset_info: DatasetInfo = {
            "dataset_id": dataset_id,
            "title": title,
            "description": description,
            "publisher_id": publisher_id,
            "topic": topic,
            "format": format,
            "access_methods": access_methods,
            "release_date": release_date,
            "update_frequency": update_frequency,
            "license": license
        }
        self.datasets[dataset_id] = dataset_info
        return { "success": True, "message": f"Dataset {dataset_id} added." }

    def update_dataset(self, dataset_id: str, updates: dict) -> dict:
        """
        Update fields of an existing dataset, enforcing catalog constraints.

        Args:
            dataset_id (str): The identifier of the dataset to update.
            updates (dict): Dictionary of fields and their new values.
                Allowed fields: title, description, publisher_id, topic, format,
                               access_methods, release_date, update_frequency, license

        Returns:
            dict:
              - On success: { "success": True, "message": "Dataset updated successfully." }
              - On error: { "success": False, "error": "<reason>" }

        Constraints:
            - The dataset must exist.
            - The new publisher_id (if provided) must exist in publishers.
            - All topic ids (if provided) must exist in topics.
            - The new format (if provided) must exist in formats.
            - All access_method ids (if provided) must exist in access_methods and list must not be empty.
            - dataset_id field cannot be updated.
        """
        # Ensure the dataset exists
        if dataset_id not in self.datasets:
            return {"success": False, "error": "Dataset does not exist."}
    
        dataset = self.datasets[dataset_id]

        # Disallow updating dataset_id itself
        if 'dataset_id' in updates:
            return {"success": False, "error": "Cannot update dataset_id."}

        # Check for publisher_id constraint
        if 'publisher_id' in updates:
            new_publisher_id = updates['publisher_id']
            if new_publisher_id not in self.publishers:
                return {"success": False, "error": "Invalid publisher_id: publisher does not exist."}

        # Check topics constraint
        if 'topic' in updates:
            topics = updates['topic']
            if not isinstance(topics, list) or not all(isinstance(t, str) for t in topics):
                return {"success": False, "error": "topic must be a list of topic_ids."}
            for topic_id in topics:
                if topic_id not in self.topics:
                    return {"success": False, "error": f"Invalid topic_id: {topic_id}"}
    
        # Check format constraint
        if 'format' in updates:
            fmt = updates['format']
            if fmt not in self.formats:
                return {"success": False, "error": "Invalid format: format_id does not exist."}
            
        # Check access_methods constraint
        if 'access_methods' in updates:
            access_methods = updates['access_methods']
            if not isinstance(access_methods, list) or len(access_methods) == 0:
                return {"success": False, "error": "access_methods must be a non-empty list of access_method_ids."}
            for am_id in access_methods:
                if am_id not in self.access_methods:
                    return {"success": False, "error": f"Invalid access_method_id: {am_id}"}

        # Apply updates
        allowed_fields = {"title", "description", "publisher_id", "topic", "format",
                         "access_methods", "release_date", "update_frequency", "license"}
        for key, value in updates.items():
            if key in allowed_fields:
                dataset[key] = value
            else:
                # Ignore or flag extra fields
                pass

        return {"success": True, "message": "Dataset updated successfully."}

    def remove_dataset(self, dataset_id: str) -> dict:
        """
        Remove a dataset from the catalog.

        Args:
            dataset_id (str): Identifier of the dataset to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Dataset <dataset_id> removed from the catalog."
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - The dataset must exist in the catalog.
        """
        if dataset_id not in self.datasets:
            return { "success": False, "error": f"Dataset '{dataset_id}' does not exist." }
    
        del self.datasets[dataset_id]
        return { "success": True, "message": f"Dataset '{dataset_id}' removed from the catalog." }

    def add_topic(self, topic_id: str, name: str, description: str) -> dict:
        """
        Add a new topic for categorizing datasets.

        Args:
            topic_id (str): Unique identifier for the topic.
            name (str): Human-readable topic name.
            description (str): Description of the topic's scope.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Topic <topic_id> added successfully."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Reason for failure"
                    }

        Constraints:
            - topic_id must be unique (not already present in self.topics).
            - All fields required (topic_id, name, description).
        """
        if not topic_id or not name or not description:
            return { "success": False, "error": "All fields (topic_id, name, description) are required." }
        if topic_id in self.topics:
            return { "success": False, "error": f"Topic with id '{topic_id}' already exists." }
        topic_info = {
            "topic_id": topic_id,
            "name": name,
            "description": description
        }
        self.topics[topic_id] = topic_info
        return { "success": True, "message": f"Topic '{topic_id}' added successfully." }

    def update_topic(self, topic_id: str, name: str = None, description: str = None) -> dict:
        """
        Update information for an existing topic.

        Args:
            topic_id (str): The identifier of the topic to update.
            name (str, optional): New name for the topic.
            description (str, optional): New description for the topic.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "message": "Topic <topic_id> updated."
                    }
                On failure:
                    {
                        "success": False,
                        "error": <reason>
                    }

        Constraints:
            - The topic must exist (topic_id present in self.topics).
            - At least one update field (name, description) must be provided.
        """
        if topic_id not in self.topics:
            return {"success": False, "error": f"Topic with id '{topic_id}' does not exist."}

        if name is None and description is None:
            return {"success": False, "error": "No update field provided (name and description are both missing)."}

        topic = self.topics[topic_id]
        if name is not None:
            topic["name"] = name
        if description is not None:
            topic["description"] = description

        return {"success": True, "message": f"Topic {topic_id} updated."}

    def add_format(
        self, 
        format_id: str, 
        name: str, 
        description: str, 
        mime_type: str
    ) -> dict:
        """
        Add a new format option for datasets.

        Args:
            format_id (str): Unique identifier for the format.
            name (str): Human-readable format name.
            description (str): Format description.
            mime_type (str): The internet media type for this format.
    
        Returns:
            dict: {
                "success": True,
                "message": "Format <format_id> added successfully."
            } 
            or 
            {
                "success": False,
                "error": "error message"
            }

        Constraints:
            - format_id must be unique (not already present in self.formats).
            - All attributes must be non-empty/non-blank.
        """
        if not all([format_id, name, description, mime_type]):
            return {"success": False, "error": "Missing required format attribute(s)."}

        if format_id in self.formats:
            return {"success": False, "error": "Format ID already exists."}

        self.formats[format_id] = {
            "format_id": format_id,
            "name": name,
            "description": description,
            "mime_type": mime_type
        }

        return {"success": True, "message": f"Format {format_id} added successfully."}

    def update_format(
        self,
        format_id: str,
        name: str = None,
        description: str = None,
        mime_type: str = None
    ) -> dict:
        """
        Update information for an existing format.

        Args:
            format_id (str): The unique identifier of the format to update.
            name (str, optional): The new name for the format.
            description (str, optional): The new description for the format.
            mime_type (str, optional): The new MIME type for the format.

        Returns:
            dict:
                - If success: {"success": True, "message": "Format updated successfully."}
                - If failure: {"success": False, "error": "reason"}

        Constraints:
            - The specified format must exist in the catalog.
            - At least one field to update should be provided.
        """
        if format_id not in self.formats:
            return {"success": False, "error": "Format not found."}

        if name is None and description is None and mime_type is None:
            return {"success": False, "error": "No updates provided."}

        format_info = self.formats[format_id]

        if name is not None:
            format_info["name"] = name
        if description is not None:
            format_info["description"] = description
        if mime_type is not None:
            format_info["mime_type"] = mime_type

        self.formats[format_id] = format_info  # Explicitly save back

        return {"success": True, "message": "Format updated successfully."}

    def add_access_method(
        self, 
        access_method_id: str, 
        type: str, 
        url: str, 
        authentication_required: bool
    ) -> dict:
        """
        Add a new access method for dataset access.

        Args:
            access_method_id (str): Unique identifier for the access method to be added.
            type (str): Type of access (e.g., 'API', 'Direct Download').
            url (str): The URL endpoint for the access method.
            authentication_required (bool): Whether authentication is required for access.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Access method added successfully." }
                - On failure: { "success": False, "error": <error message> }

        Constraints:
            - access_method_id must be unique (not already present).
            - All parameters are required and must be of appropriate types.
        """
        if not all([access_method_id, type, url]) or not isinstance(authentication_required, bool):
            return { "success": False, "error": "All parameters are required and must have correct types." }
    
        if access_method_id in self.access_methods:
            return { "success": False, "error": "Access method ID already exists." }

        self.access_methods[access_method_id] = {
            "access_method_id": access_method_id,
            "type": type,
            "url": url,
            "authentication_required": authentication_required
        }
        return { "success": True, "message": "Access method added successfully." }

    def update_access_method(
        self,
        access_method_id: str,
        type: str = None,
        url: str = None,
        authentication_required: bool = None
    ) -> dict:
        """
        Update information for an existing access method.

        Args:
            access_method_id (str): The ID of the access method to update.
            type (str, optional): New type for the access method.
            url (str, optional): New URL for the access method.
            authentication_required (bool, optional): Whether authentication is required.

        Returns:
            dict:
                success (bool): Whether operation succeeded.
                message (str): Success message if successful.
                error (str): Error message if not successful.

        Constraints:
            - The access method must exist.
            - At least one field must be provided for update.
        """
        if access_method_id not in self.access_methods:
            return {"success": False, "error": "Access method not found."}

        # Nothing to update?
        if type is None and url is None and authentication_required is None:
            return {"success": False, "error": "No fields to update."}

        am = self.access_methods[access_method_id]

        if type is not None:
            am["type"] = type
        if url is not None:
            am["url"] = url
        if authentication_required is not None:
            am["authentication_required"] = authentication_required

        self.access_methods[access_method_id] = am  # assignment may be redundant but is clear
        return {"success": True, "message": f"Access method {access_method_id} updated."}


class GovernmentOpenDataCatalog(BaseEnv):
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

    def list_publishers(self, **kwargs):
        return self._call_inner_tool('list_publishers', kwargs)

    def get_publisher_by_id(self, **kwargs):
        return self._call_inner_tool('get_publisher_by_id', kwargs)

    def list_publishers_by_country(self, **kwargs):
        return self._call_inner_tool('list_publishers_by_country', kwargs)

    def get_dataset_by_id(self, **kwargs):
        return self._call_inner_tool('get_dataset_by_id', kwargs)

    def list_datasets(self, **kwargs):
        return self._call_inner_tool('list_datasets', kwargs)

    def list_datasets_by_publisher(self, **kwargs):
        return self._call_inner_tool('list_datasets_by_publisher', kwargs)

    def list_datasets_by_topic(self, **kwargs):
        return self._call_inner_tool('list_datasets_by_topic', kwargs)

    def list_datasets_by_format(self, **kwargs):
        return self._call_inner_tool('list_datasets_by_format', kwargs)

    def list_datasets_by_access_method(self, **kwargs):
        return self._call_inner_tool('list_datasets_by_access_method', kwargs)

    def list_topics(self, **kwargs):
        return self._call_inner_tool('list_topics', kwargs)

    def get_topic_by_id(self, **kwargs):
        return self._call_inner_tool('get_topic_by_id', kwargs)

    def list_formats(self, **kwargs):
        return self._call_inner_tool('list_formats', kwargs)

    def get_format_by_id(self, **kwargs):
        return self._call_inner_tool('get_format_by_id', kwargs)

    def list_access_methods(self, **kwargs):
        return self._call_inner_tool('list_access_methods', kwargs)

    def get_access_method_by_id(self, **kwargs):
        return self._call_inner_tool('get_access_method_by_id', kwargs)

    def list_datasets_by_release_date(self, **kwargs):
        return self._call_inner_tool('list_datasets_by_release_date', kwargs)

    def list_datasets_by_update_frequency(self, **kwargs):
        return self._call_inner_tool('list_datasets_by_update_frequency', kwargs)

    def list_datasets_by_license(self, **kwargs):
        return self._call_inner_tool('list_datasets_by_license', kwargs)

    def add_publisher(self, **kwargs):
        return self._call_inner_tool('add_publisher', kwargs)

    def update_publisher(self, **kwargs):
        return self._call_inner_tool('update_publisher', kwargs)

    def remove_publisher(self, **kwargs):
        return self._call_inner_tool('remove_publisher', kwargs)

    def add_dataset(self, **kwargs):
        return self._call_inner_tool('add_dataset', kwargs)

    def update_dataset(self, **kwargs):
        return self._call_inner_tool('update_dataset', kwargs)

    def remove_dataset(self, **kwargs):
        return self._call_inner_tool('remove_dataset', kwargs)

    def add_topic(self, **kwargs):
        return self._call_inner_tool('add_topic', kwargs)

    def update_topic(self, **kwargs):
        return self._call_inner_tool('update_topic', kwargs)

    def add_format(self, **kwargs):
        return self._call_inner_tool('add_format', kwargs)

    def update_format(self, **kwargs):
        return self._call_inner_tool('update_format', kwargs)

    def add_access_method(self, **kwargs):
        return self._call_inner_tool('add_access_method', kwargs)

    def update_access_method(self, **kwargs):
        return self._call_inner_tool('update_access_method', kwargs)

