# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, Any, TypedDict



class URLRecordInfo(TypedDict):
    l_id: str        # Internal ID for the URL
    url: str         # The unique URL
    metadata: Dict[str, Any]    # Metadata about the URL

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Backend database for URL management.
        """

        # URL Records: {l_id: URLRecordInfo}
        self.url_records: Dict[str, URLRecordInfo] = {}

        # Constraints:
        # - URLs must be unique within the system (no duplicate URL records).
        # - Each URL must be associated with one (and only one) internal ID.
        # - Queries must match exactly or according to predefined matching rules (e.g., case-sensitivity, normalization).
        # - Metadata fields (if present) must adhere to defined formats and validation rules.

    def get_url_record_by_url(self, url: str) -> dict:
        """
        Retrieve a URL record using exact or rule-based matching on the URL field.

        Args:
            url (str): The URL to search for.

        Returns:
            dict: 
                - {
                    "success": True,
                    "data": URLRecordInfo  # The full record for the matching URL
                  }
                - or {
                    "success": False,
                    "error": "URL record not found"
                  }

        Constraints:
            - Matching is exact unless further rules are specified.
            - URLs must be unique in the system.
        """
        for record in self.url_records.values():
            if record["url"] == url:
                return { "success": True, "data": record }
        return { "success": False, "error": "URL record not found" }

    def get_url_record_by_id(self, l_id: str) -> dict:
        """
        Retrieve a URL record (url, metadata) given its unique internal ID (l_id).

        Args:
            l_id (str): The internal unique identifier of the URL record.

        Returns:
            dict: {
                "success": True,
                "data": URLRecordInfo  # Complete info for the URL record
            }
            or
            {
                "success": False,
                "error": str  # Description of error if not found
            }

        Constraints:
            - l_id must exist in the database; otherwise, error should be returned.
            - No permission checks or normalization are performed.
        """
        record = self.url_records.get(l_id)
        if record is None:
            return { "success": False, "error": "URL record not found" }
        return { "success": True, "data": record }

    def get_internal_id_by_url(self, url: str) -> dict:
        """
        Retrieve only the internal ID (l_id) for a given URL.

        Args:
            url (str): The URL for which to retrieve the internal ID.

        Returns:
            dict: 
                { "success": True, "data": str }                  # The l_id if found
                or
                { "success": False, "error": "URL not found" }    # If no match

        Constraints:
            - Matches according to the system's matching rules (default: exact, case-sensitive).
            - URLs in the system are unique.
        """
        for record in self.url_records.values():
            if record["url"] == url:
                return { "success": True, "data": record["l_id"] }
        return { "success": False, "error": "URL not found" }

    def search_urls_by_metadata(self, metadata_filter: dict) -> dict:
        """
        Find all URL records that match the supplied metadata attribute values.

        Args:
            metadata_filter (dict): Key-value pairs that must be exactly matched in the metadata of each URL record.

        Returns:
            dict: {
                "success": True,
                "data": [URLRecordInfo, ...]  # All matching URL records (list may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Description of error, e.g., input not dict or empty filter
            }

        Constraints:
            - Metadata filter must be a non-empty dictionary.
            - Each URL record's 'metadata' must contain the keys with exactly matching values.
        """
        if not isinstance(metadata_filter, dict) or not metadata_filter:
            return { "success": False, "error": "Metadata filter must be a non-empty dictionary" }

        matching_records = []
        for rec in self.url_records.values():
            meta = rec.get("metadata", {})
            if all(meta.get(k) == v for k, v in metadata_filter.items()):
                matching_records.append(rec)

        return { "success": True, "data": matching_records }

    def list_all_urls(self) -> dict:
        """
        Retrieve a complete list of all URL records in the system.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[URLRecordInfo],  # All URLRecordInfo dicts currently in the system. May be empty.
                }
        Constraints:
            - Returns all URL records, does not filter or error if empty.
        """
        all_records = list(self.url_records.values())
        return { "success": True, "data": all_records }

    def add_url_record(self, l_id: str, url: str, metadata: dict) -> dict:
        """
        Insert a new URL record with the provided internal ID, URL, and metadata.

        Args:
            l_id (str): Internal identifier for the URL (must be unique).
            url (str): The URL to add (must be unique).
            metadata (dict): Metadata dictionary associated with the URL. Must be a dict.

        Returns:
            dict: On success:
                    {
                        "success": True,
                        "message": "URL record added successfully"
                    }
                  On failure:
                    {
                        "success": False,
                        "error": <reason>
                    }

        Constraints:
            - URL and l_id must be unique in the system.
            - Metadata must be a dict (further format validation can be added if needed).
        """
        # Check if l_id already exists
        if l_id in self.url_records:
            return {"success": False, "error": "Internal ID already exists"}

        # Check for duplicate URL (any record with this url)
        for record in self.url_records.values():
            if record['url'] == url:
                return {"success": False, "error": "URL already exists in the system"}

        # Validate metadata is a dictionary
        if not isinstance(metadata, dict):
            return {"success": False, "error": "Metadata must be a dictionary"}

        # (Optional: more metadata format validation could go here)

        # Add record
        self.url_records[l_id] = {
            "l_id": l_id,
            "url": url,
            "metadata": metadata
        }

        return {"success": True, "message": "URL record added successfully"}

    def update_url_metadata(self, new_metadata: dict, l_id: str = None, url: str = None) -> dict:
        """
        Update the metadata of a URL record, identified by l_id or URL.
        Ensures metadata validation rules are met before updating.
    
        Args:
            new_metadata (dict): Metadata dictionary to update in the record.
            l_id (str, optional): The internal ID for the URL.
            url (str, optional): The URL string itself.
    
        Returns:
            dict: 
                { "success": True, "message": "Metadata for URL record updated successfully" }
                or
                { "success": False, "error": "reason" }
    
        Constraints:
            - Either l_id or url must be provided.
            - Metadata must adhere to defined formats/validation rules.
        """
        # Ensure input validity
        if not l_id and not url:
            return { "success": False, "error": "Must provide either l_id or url for record identification" }
    
        # Find the record
        record = None
        if l_id:
            record = self.url_records.get(l_id)
        elif url:
            # URLs must be unique
            for rec in self.url_records.values():
                if rec["url"] == url:
                    record = rec
                    break

        # If both provided, check consistency
        if l_id and url:
            if record and record.get("url") != url:
                return { "success": False, "error": "Provided l_id and url do not match the same record" }
            # If not found by l_id, try finding by url
            if not record:
                for rec in self.url_records.values():
                    if rec["url"] == url:
                        record = rec
                        break
                if record and record.get("l_id") != l_id:
                    return { "success": False, "error": "Provided l_id and url do not match the same record" }

        if not record:
            return { "success": False, "error": "No matching URL record found" }
    
        # --- Metadata validation placeholder ---
        # Replace the next lines with custom logic as needed
        valid = isinstance(new_metadata, dict)
        if not valid:
            return { "success": False, "error": "Metadata must be a dictionary" }
        # Example: check for reserved keys or required fields (customize as per real validation)
        # if "creation_date" in new_metadata and not isinstance(new_metadata["creation_date"], str):
        #     return { "success": False, "error": "Invalid creation_date format" }

        # Update the metadata for the record (overwrite)
        record["metadata"] = new_metadata

        # Ensure the main database copy is updated
        self.url_records[record["l_id"]] = record

        return { "success": True, "message": "Metadata for URL record updated successfully" }

    def delete_url_record(self, l_id: str = None, url: str = None) -> dict:
        """
        Remove a URL record from the database, by internal ID (l_id) or URL.

        Args:
            l_id (str, optional): Internal ID of the URL record to delete.
            url (str, optional): The URL of the record to delete.

        Returns:
            dict: {
                "success": True,
                "message": str describing the deletion
            }
            or
            {
                "success": False,
                "error": str error message
            }

        Constraints:
            - Either l_id or url must be specified (at least one).
            - If both are specified, they must refer to the same record.
            - The target record must exist.
            - Deletion removes the record and maintains URL uniqueness invariants.
        """
        if l_id is None and url is None:
            return {"success": False, "error": "Must specify either l_id or url for deletion"}

        record_lid = None
        record_url = None

        # Try to resolve the record by l_id
        if l_id is not None:
            record = self.url_records.get(l_id)
            if not record:
                return {"success": False, "error": f"URL record with l_id '{l_id}' does not exist"}
            record_url = record["url"]

        # Try to resolve by URL if url is specified
        if url is not None:
            resolved_lid = None
            for rec_id, rec in self.url_records.items():
                if rec["url"] == url:
                    resolved_lid = rec_id
                    break
            if resolved_lid is None:
                return {"success": False, "error": f"URL record with url '{url}' does not exist"}
            record_lid = resolved_lid

        # If both l_id and url are specified, check they refer to the same record
        if l_id is not None and url is not None:
            if l_id != record_lid:
                return {"success": False, "error": "Provided l_id and url refer to different records"}

        # Decide which l_id to use for deletion
        lid_to_delete = l_id if l_id is not None else record_lid

        # Perform the deletion
        rec = self.url_records.pop(lid_to_delete, None)
        if rec:
            return {
                "success": True,
                "message": f"URL record deleted: l_id='{lid_to_delete}', url='{rec['url']}'"
            }
        else:
            return {"success": False, "error": "Unexpected error deleting URL record"}

    def normalize_and_update_url(self, l_id: str) -> dict:
        """
        Normalize the URL for the record identified by `l_id` according to predefined rules, and update the record.
    
        Args:
            l_id (str): The internal ID of the URL record to update.

        Returns:
            dict: On success, {"success": True, "message": "URL normalized and updated"}
                  On failure, {"success": False, "error": <reason>}
    
        Constraints:
            - URLs must remain unique post-normalization.
            - If the normalized URL collides with another record's URL, operation must fail.
            - If l_id does not exist, operation must fail.
            - Normalization rules are assumed basic: lowercasing and trimming whitespace and removing trailing slash.
        """
        def _normalize(url: str) -> str:
            # Example normalization: strip spaces, lower-case, remove trailing slash
            normalized = url.strip().lower()
            if normalized.endswith('/'):
                normalized = normalized.rstrip('/')
            return normalized

        # Check if the record exists
        if l_id not in self.url_records:
            return {"success": False, "error": "URL record not found"}

        record = self.url_records[l_id]
        old_url = record['url']
        normalized_url = _normalize(old_url)

        # If the URL is unchanged, do nothing
        if normalized_url == old_url:
            return {"success": True, "message": "URL already normalized"}

        # Check for uniqueness (excluding current record)
        for rec_id, rec in self.url_records.items():
            if rec_id != l_id and _normalize(rec['url']) == normalized_url:
                return {
                    "success": False,
                    "error": "Normalized URL would collide with another record"
                }

        # Update the record
        self.url_records[l_id]['url'] = normalized_url
        return {"success": True, "message": "URL normalized and updated"}

    def bulk_insert_url_records(self, records: list[dict]) -> dict:
        """
        Insert multiple new URL records (l_id, url, metadata) at once.
        Ensures:
          - No duplicate URLs in the system (existing or within batch).
          - Each URL must be non-empty and unique.
          - l_id must be unique in the system and within the batch.
          - Metadata must be a dictionary.

        Args:
            records (list of dict): Each dict should include:
                - 'l_id' (str): Internal unique ID.
                - 'url' (str): Unique URL.
                - 'metadata' (dict): Metadata.

        Returns:
            dict: {
                "success": True,
                "message": str,  # Status summary
                "inserted": list of l_id actually inserted,
                "skipped": list of {l_id, url, reason} for skipped records,
            }
            or
            {
                "success": False,
                "error": str
            }
        """
        if not isinstance(records, list):
            return { "success": False, "error": "Input must be a list of records." }

        # Gather existing URLs and l_ids
        existing_urls = set(rec["url"] for rec in self.url_records.values())
        existing_lids = set(self.url_records.keys())
        batch_urls = set()
        batch_lids = set()

        inserted = []
        skipped = []

        for idx, rec in enumerate(records):
            rec_lid = rec.get("l_id")
            rec_url = rec.get("url")
            rec_meta = rec.get("metadata")

            # Field validation
            if rec_lid is None or rec_url is None or rec_meta is None:
                skipped.append({
                    "l_id": rec_lid,
                    "url": rec_url,
                    "reason": "Missing required field(s)"
                })
                continue

            # Type validation
            if not isinstance(rec_lid, str) or not isinstance(rec_url, str) or not isinstance(rec_meta, dict):
                skipped.append({
                    "l_id": rec_lid,
                    "url": rec_url,
                    "reason": "Invalid field types"
                })
                continue
        
            # Uniqueness checks
            if rec_url in existing_urls or rec_url in batch_urls:
                skipped.append({
                    "l_id": rec_lid,
                    "url": rec_url,
                    "reason": "Duplicate URL"
                })
                continue

            if rec_lid in existing_lids or rec_lid in batch_lids:
                skipped.append({
                    "l_id": rec_lid,
                    "url": rec_url,
                    "reason": "Duplicate l_id"
                })
                continue

            # If all checks pass, insert
            self.url_records[rec_lid] = {
                "l_id": rec_lid,
                "url": rec_url,
                "metadata": rec_meta
            }
            inserted.append(rec_lid)
            batch_urls.add(rec_url)
            batch_lids.add(rec_lid)

        successes = len(inserted)
        failures = len(skipped)
        message = f"{successes} records inserted, {failures} skipped."

        return {
            "success": True,
            "message": message,
            "inserted": inserted,
            "skipped": skipped
        }


class URLManagementDatabase(BaseEnv):
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

    def get_url_record_by_url(self, **kwargs):
        return self._call_inner_tool('get_url_record_by_url', kwargs)

    def get_url_record_by_id(self, **kwargs):
        return self._call_inner_tool('get_url_record_by_id', kwargs)

    def get_internal_id_by_url(self, **kwargs):
        return self._call_inner_tool('get_internal_id_by_url', kwargs)

    def search_urls_by_metadata(self, **kwargs):
        return self._call_inner_tool('search_urls_by_metadata', kwargs)

    def list_all_urls(self, **kwargs):
        return self._call_inner_tool('list_all_urls', kwargs)

    def add_url_record(self, **kwargs):
        return self._call_inner_tool('add_url_record', kwargs)

    def update_url_metadata(self, **kwargs):
        return self._call_inner_tool('update_url_metadata', kwargs)

    def delete_url_record(self, **kwargs):
        return self._call_inner_tool('delete_url_record', kwargs)

    def normalize_and_update_url(self, **kwargs):
        return self._call_inner_tool('normalize_and_update_url', kwargs)

    def bulk_insert_url_records(self, **kwargs):
        return self._call_inner_tool('bulk_insert_url_records', kwargs)

