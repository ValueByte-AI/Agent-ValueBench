# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
from typing import Optional
from datetime import datetime
from typing import Optional, Dict



class DomainInfo(TypedDict):
    domain_name: str
    threat_status: str  # "malicious", "safe", or "unknown"
    detection_date: str
    classification: str
    source: str

class EmailAddressInfo(TypedDict):
    mail_address: str
    threat_status: str  # "malicious", "safe", or "unknown"
    detection_date: str
    classification: str
    source: str

class URLInfo(TypedDict):
    url: str
    threat_status: str  # "malicious", "safe", or "unknown"
    detection_date: str
    classification: str
    source: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Anti-phishing threat intelligence database state.
        """

        # Domains: {domain_name: DomainInfo}
        self.domains: Dict[str, DomainInfo] = {}
        # Maps to entity: Doma, attributes: domain_name, threat_status, detection_date, classification, source

        # Email addresses: {mail_address: EmailAddressInfo}
        self.email_addresses: Dict[str, EmailAddressInfo] = {}
        # Maps to entity: mailAddress, attributes: mail_address, threat_status, detection_date, classification, source

        # URLs: {url: URLInfo}
        self.urls: Dict[str, URLInfo] = {}
        # Maps to entity: URL, attributes: url, threat_status, detection_date, classification, source

        # Constraint notes:
        # - Each entity (domain, email address, URL) must have a unique identifier.
        # - threat_status is typically "malicious", "safe", or "unknown".
        # - detection_date must be recorded for all new intelligence entries.
        # - classification refines the type of threat (e.g., phishing, malware).
        # - Entities can be updated as new intelligence arrives.

    def check_domain_presence(self, domain_name: str) -> dict:
        """
        Check if the specified domain is present in the threat intelligence database.
        If found, return its DomainInfo. If not, indicate absence.

        Args:
            domain_name (str): The domain to check for in the database.

        Returns:
            dict: {
                "success": True,
                "data": DomainInfo  # If found
            }
            or
            {
                "success": False,
                "error": str  # Explanation if not found or invalid input
            }

        Constraints:
            - domain_name must not be empty.
            - Presence is exactly by string match.
        """
        if not domain_name or not isinstance(domain_name, str):
            return {"success": False, "error": "Invalid or empty domain_name was provided."}
    
        info = self.domains.get(domain_name)
        if info is not None:
            return {"success": True, "data": info}
        else:
            return {"success": False, "error": "Domain not found in database."}

    def check_email_address_presence(self, mail_address: str) -> dict:
        """
        Check if a given email address is present in the database.
        If found, return its associated threat intelligence information.

        Args:
            mail_address (str): The email address to check.

        Returns:
            dict: {
                "success": True,
                "data": EmailAddressInfo  # All intelligence on the email address
            }
            OR
            {
                "success": False,
                "error": "Email address not found"
            }

        Constraints:
            - Email address (mail_address) must match a key in the database.
        """
        info = self.email_addresses.get(mail_address)
        if info is None:
            return {"success": False, "error": "Email address not found"}
        return {"success": True, "data": info}

    def check_url_presence(self, url: str) -> dict:
        """
        Check if a given URL is present in the threat intelligence database.

        Args:
            url (str): The URL to look up.

        Returns:
            dict:
                - If found: {"success": True, "data": URLInfo}
                - If not found: {"success": False, "error": "URL not found in database"}

        Constraints:
            - URL string is matched exactly as stored in the database.
        """
        if url in self.urls:
            return {"success": True, "data": self.urls[url]}
        else:
            return {"success": False, "error": "URL not found in database"}

    def get_domain_threat_info(self, domain_name: str) -> dict:
        """
        Retrieve the full threat intelligence (status, classification, detection date, source)
        for a given domain.

        Args:
            domain_name (str): The domain to query.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "data": DomainInfo
                }
                On error:
                {
                    "success": False,
                    "error": str  # Reason, e.g. "Domain not found"
                }

        Constraints:
            - domain_name must exist in the database.
        """
        domain_info = self.domains.get(domain_name)
        if domain_info is None:
            return {"success": False, "error": "Domain not found"}

        return {"success": True, "data": domain_info}

    def get_email_address_threat_info(self, mail_address: str) -> dict:
        """
        Retrieve the complete threat intelligence entry (if present) for a given email address.

        Args:
            mail_address (str): The email address to look up in the intelligence database.

        Returns:
            dict: {
                "success": True,
                "data": EmailAddressInfo,  # Full entry for the email address
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., email address not found
            }

        Constraints:
            - mail_address must be present as a key in self.email_addresses for success.
        """
        info = self.email_addresses.get(mail_address)
        if info is None:
            return { "success": False, "error": "Email address not found in database" }
        return { "success": True, "data": info }

    def get_url_threat_info(self, url: str) -> dict:
        """
        Retrieve the full threat intelligence information for a given URL.

        Args:
            url (str): The URL to look up.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": URLInfo  # All attributes for the given URL.
                    }
                On failure:
                    {
                        "success": False,
                        "error": "URL not found"
                    }

        Constraints:
            - URLs are unique; if not found, return an appropriate error message.
            - Query is read-only; no change to internal state.
        """
        url_info = self.urls.get(url)
        if url_info is not None:
            return { "success": True, "data": url_info }
        else:
            return { "success": False, "error": "URL not found" }

    def list_domains_by_threat_status(self, threat_status: str) -> dict:
        """
        List all domains filtered by a given threat_status ('malicious', 'safe', 'unknown').

        Args:
            threat_status (str): The threat status to filter by.

        Returns:
            dict: {
                "success": True,
                "data": List[DomainInfo],   # may be empty
            }
            OR
            {
                "success": False,
                "error": str   # e.g. invalid threat_status
            }

        Constraints:
            - threat_status must be one of 'malicious', 'safe', 'unknown'.
        """
        valid_statuses = {"malicious", "safe", "unknown"}
        if threat_status not in valid_statuses:
            return {
                "success": False,
                "error": "Invalid threat_status. Must be 'malicious', 'safe', or 'unknown'."
            }
        result = [
            domain_info for domain_info in self.domains.values()
            if domain_info["threat_status"] == threat_status
        ]
        return { "success": True, "data": result }

    def list_email_addresses_by_threat_status(self, threat_status: str) -> dict:
        """
        List all email addresses filtered by a given threat_status.

        Args:
            threat_status (str): Filter value, one of "malicious", "safe", "unknown".

        Returns:
            dict:
                - If threat_status valid:
                  { "success": True, "data": List[EmailAddressInfo] }
                - If threat_status invalid:
                  { "success": False, "error": "Invalid threat_status value" }

        Constraints:
            - threat_status must be one of: "malicious", "safe", "unknown"
        """
        valid_statuses = {"malicious", "safe", "unknown"}
        if threat_status not in valid_statuses:
            return { "success": False, "error": "Invalid threat_status value" }

        result = [
            entry
            for entry in self.email_addresses.values()
            if entry["threat_status"] == threat_status
        ]
        return { "success": True, "data": result }

    def list_urls_by_threat_status(self, threat_status: str) -> dict:
        """
        List all URLs with the specified threat_status.

        Args:
            threat_status (str): The threat status filter ("malicious", "safe", or "unknown").

        Returns:
            dict: {
                "success": True,
                "data": List[URLInfo],  # May be empty if no match
            }
            or
            {
                "success": False,
                "error": str  # If an invalid threat_status is specified
            }

        Constraints:
            - Only allow threat_status values: "malicious", "safe", "unknown".
        """
        valid_statuses = {"malicious", "safe", "unknown"}
        if threat_status not in valid_statuses:
            return { "success": False, "error": "Invalid threat_status value" }

        filtered = [
            url_info for url_info in self.urls.values()
            if url_info['threat_status'] == threat_status
        ]

        return { "success": True, "data": filtered }

    def list_all_domains(self) -> dict:
        """
        Retrieve all domain intelligence entries from the database.

        Returns:
            dict: {
                "success": True,
                "data": List[DomainInfo],  # List of all domain entries; empty list if none
            }
        """
        domain_list = list(self.domains.values())
        return { "success": True, "data": domain_list }

    def list_all_email_addresses(self) -> dict:
        """
        Retrieve all email address intelligence entries in the database.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[EmailAddressInfo]  # List of all email entries; may be empty.
            }

        Constraints:
            - None; this operation performs a bulk read of all email addresses.
        """
        return {
            "success": True,
            "data": list(self.email_addresses.values())
        }

    def list_all_urls(self) -> dict:
        """
        Retrieve all URL intelligence entries in the database.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[URLInfo],  # List of all URLInfo entries (may be empty)
            }
        """
        urls_list = list(self.urls.values())
        return { "success": True, "data": urls_list }

    def add_domain_entry(
        self, 
        domain_name: str, 
        threat_status: str, 
        detection_date: str, 
        classification: str, 
        source: str
    ) -> dict:
        """
        Add a new domain intelligence entry.

        Args:
            domain_name (str): Unique domain name to add.
            threat_status (str): Threat status ("malicious", "safe", "unknown").
            detection_date (str): Date the threat was detected.
            classification (str): Threat classification.
            source (str): Source of the intelligence.

        Returns:
            dict: 
                On success: {"success": True, "message": "Domain entry added successfully"}
                On failure: {"success": False, "error": <reason>}

        Constraints:
            - domain_name must be unique.
            - threat_status must be "malicious", "safe", or "unknown".
            - detection_date, classification, source must be provided (non-empty).
        """

        # Check for required fields
        if not domain_name:
            return { "success": False, "error": "Missing required field: domain_name" }
        if not threat_status:
            return { "success": False, "error": "Missing required field: threat_status" }
        if not detection_date:
            return { "success": False, "error": "Missing required field: detection_date" }
        if not classification:
            return { "success": False, "error": "Missing required field: classification" }
        if not source:
            return { "success": False, "error": "Missing required field: source" }

        # Check uniqueness
        if domain_name in self.domains:
            return { "success": False, "error": "Domain already exists" }

        # Validate threat_status
        allowed_statuses = {"malicious", "safe", "unknown"}
        if threat_status not in allowed_statuses:
            return { "success": False, "error": "Invalid threat status" }

        # Add the entry
        self.domains[domain_name] = {
            "domain_name": domain_name,
            "threat_status": threat_status,
            "detection_date": detection_date,
            "classification": classification,
            "source": source
        }

        return { "success": True, "message": "Domain entry added successfully" }

    def add_email_address_entry(
        self,
        mail_address: str,
        threat_status: str,
        detection_date: str,
        classification: str,
        source: str
    ) -> dict:
        """
        Add a new email address threat intelligence entry.

        Args:
            mail_address (str): Email address (must be unique).
            threat_status (str): "malicious", "safe", or "unknown".
            detection_date (str): ISO date string or similar, must not be empty.
            classification (str): Threat classification (e.g., phishing, malware).
            source (str): Source of the threat intelligence.

        Returns:
            dict: {
                "success": True,
                "message": "Email address entry added successfully"
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - mail_address must be unique (not already present).
            - threat_status must be one of "malicious", "safe", "unknown".
            - detection_date must be provided and non-empty.
            - classification and source must be provided and non-empty.
        """
        allowed_statuses = {"malicious", "safe", "unknown"}
        if not mail_address or mail_address in self.email_addresses:
            return {"success": False, "error": "Email address already exists or is invalid"}
        if threat_status not in allowed_statuses:
            return {"success": False, "error": "Invalid threat_status; must be 'malicious', 'safe', or 'unknown'"}
        if not detection_date:
            return {"success": False, "error": "Missing detection_date"}
        if not classification:
            return {"success": False, "error": "Missing classification"}
        if not source:
            return {"success": False, "error": "Missing source"}

        self.email_addresses[mail_address] = {
            "mail_address": mail_address,
            "threat_status": threat_status,
            "detection_date": detection_date,
            "classification": classification,
            "source": source
        }

        return {"success": True, "message": "Email address entry added successfully"}

    def add_url_entry(
        self,
        url: str,
        threat_status: str,
        detection_date: str,
        classification: str,
        source: str
    ) -> dict:
        """
        Add a new URL intelligence entry to the database.

        Args:
            url (str): The URL to add. Must be unique in the database.
            threat_status (str): The threat status for this URL. Must be "malicious", "safe", or "unknown".
            detection_date (str): Detection date for this entry (ISO format or similar). Required.
            classification (str): Threat classification ("phishing", "malware", etc.).
            source (str): The source of the intelligence.

        Returns:
            dict:
                On success:  { "success": True, "message": "URL entry added." }
                On failure:  { "success": False, "error": "..." }

        Constraints:
            - URL must not already exist.
            - threat_status in {"malicious", "safe", "unknown"}.
            - detection_date must be provided.
        """
        # Check for required fields
        if not url or not isinstance(url, str):
            return { "success": False, "error": "URL must be a non-empty string." }
        if url in self.urls:
            return { "success": False, "error": "URL entry already exists." }
        if threat_status not in {"malicious", "safe", "unknown"}:
            return { "success": False, "error": "threat_status must be 'malicious', 'safe', or 'unknown'." }
        if not detection_date or not isinstance(detection_date, str):
            return { "success": False, "error": "detection_date must be provided and non-empty." }
        if not classification or not isinstance(classification, str):
            return { "success": False, "error": "classification must be provided and non-empty." }
        if not source or not isinstance(source, str):
            return { "success": False, "error": "source must be provided and non-empty." }

        # Add the entry
        self.urls[url] = {
            "url": url,
            "threat_status": threat_status,
            "detection_date": detection_date,
            "classification": classification,
            "source": source
        }

        return { "success": True, "message": "URL entry added." }


    def update_domain_entry(
        self, 
        domain_name: str,
        threat_status: Optional[str] = None,
        detection_date: Optional[str] = None,
        classification: Optional[str] = None,
        source: Optional[str] = None
    ) -> dict:
        """
        Update one or more attributes (threat_status, detection_date, classification, source) of an existing domain entry.

        Args:
            domain_name (str): The domain to update.
            threat_status (Optional[str]): New threat status ("malicious", "safe", or "unknown"), if updating.
            detection_date (Optional[str]): New detection date, if updating.
            classification (Optional[str]): New classification, if updating.
            source (Optional[str]): New source, if updating.

        Returns:
            dict:
                On success: { "success": True, "message": "Domain entry updated." }
                On failure: { "success": False, "error": str }

        Constraints:
            - The domain must exist.
            - threat_status (if specified) must be "malicious", "safe", or "unknown".
            - At least one attribute to update must be specified.
        """
        if domain_name not in self.domains:
            return {"success": False, "error": "Domain not found."}
    
        if all(v is None for v in [threat_status, detection_date, classification, source]):
            return {"success": False, "error": "No update fields provided."}
    
        valid_status = {"malicious", "safe", "unknown"}
        if threat_status is not None and threat_status not in valid_status:
            return {"success": False, "error": "Invalid threat_status value."}
    
        # Update attributes as provided
        if threat_status is not None:
            self.domains[domain_name]["threat_status"] = threat_status
        if detection_date is not None:
            self.domains[domain_name]["detection_date"] = detection_date
        if classification is not None:
            self.domains[domain_name]["classification"] = classification
        if source is not None:
            self.domains[domain_name]["source"] = source

        return {"success": True, "message": "Domain entry updated."}

    def update_email_address_entry(
        self,
        mail_address: str,
        threat_status: str = None,
        detection_date: str = None,
        classification: str = None,
        source: str = None
    ) -> dict:
        """
        Update any subset of attributes for an existing email address entry.
        Cannot update the mail_address itself.

        Args:
            mail_address (str): The unique identifier for the email address to update.
            threat_status (str, optional): New threat status; must be "malicious", "safe", or "unknown".
            detection_date (str, optional): New detection date.
            classification (str, optional): New classification.
            source (str, optional): New source string.

        Returns:
            dict: {
                "success": True,
                "message": "Email address entry updated successfully."
            }
            or
            {
                "success": False,
                "error": error message
            }

        Constraints:
            - Email address must already exist.
            - Only updates allowed for threat_status, detection_date, classification, source.
            - If threat_status is provided, it must be "malicious", "safe", or "unknown".
        """
        entry = self.email_addresses.get(mail_address)
        if entry is None:
            return { "success": False, "error": "Email address entry does not exist." }

        allowed_statuses = {"malicious", "safe", "unknown"}

        # Validate and apply updates
        if threat_status is not None:
            if threat_status not in allowed_statuses:
                return { "success": False, "error": f"Invalid threat_status '{threat_status}'." }
            entry["threat_status"] = threat_status

        if detection_date is not None:
            entry["detection_date"] = detection_date

        if classification is not None:
            entry["classification"] = classification

        if source is not None:
            entry["source"] = source

        # Save updated entry back (optional, since dict is mutable)
        self.email_addresses[mail_address] = entry

        return { "success": True, "message": "Email address entry updated successfully." }

    def update_url_entry(
        self,
        url: str,
        threat_status: str = None,
        detection_date: str = None,
        classification: str = None,
        source: str = None
    ) -> dict:
        """
        Update any of the attributes for an existing URL entry.

        Args:
            url (str): Unique identifier for the URL entry.
            threat_status (str, optional): New threat status ("malicious", "safe", or "unknown").
            detection_date (str, optional): Updated detection date (ISO string or similar).
            classification (str, optional): Updated threat classification.
            source (str, optional): Updated source information.

        Returns:
            dict:
                On success:
                    {'success': True, 'message': 'URL entry updated.'}
                On failure:
                    {'success': False, 'error': <reason>}

        Constraints:
            - The URL entry must already exist in the database.
            - At least one attribute must be provided for update.
            - Only updates provided attributes; all others remain unchanged.
        """
        # Check if entry exists
        if url not in self.urls:
            return { "success": False, "error": "URL entry does not exist." }

        allowed_statuses = {"malicious", "safe", "unknown"}
        if threat_status is not None and threat_status not in allowed_statuses:
            return {
                "success": False,
                "error": "Invalid threat_status; must be 'malicious', 'safe', or 'unknown'."
            }

        # Track if any update is actually performed
        updated = False
        entry = self.urls[url]

        update_fields = {
            "threat_status": threat_status,
            "detection_date": detection_date,
            "classification": classification,
            "source": source
        }
        # Only update fields that are not None
        for key, value in update_fields.items():
            if value is not None:
                entry[key] = value
                updated = True

        if not updated:
            return { "success": False, "error": "No update fields provided." }

        # Save back (not strictly necessary for dict, but good pattern)
        self.urls[url] = entry

        return { "success": True, "message": "URL entry updated." }

    def reclassify_domain_status(
        self,
        domain_name: str,
        threat_status: str = None,
        classification: str = None
    ) -> dict:
        """
        Change the threat_status and/or classification for an existing domain entry.

        Args:
            domain_name (str): The unique domain name to reclassify.
            threat_status (Optional[str]): The new threat status ("malicious", "safe", or "unknown"). If omitted, leaves unchanged.
            classification (Optional[str]): The new threat classification. If omitted, leaves unchanged.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Domain threat status and/or classification updated." }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - Domain must already exist.
            - threat_status must be "malicious", "safe", or "unknown" if provided.
            - At least one of threat_status/classification must be specified.
        """
        if domain_name not in self.domains:
            return { "success": False, "error": "Domain not found." }

        if threat_status is None and classification is None:
            return { "success": False, "error": "No changes specified." }

        valid_statuses = {"malicious", "safe", "unknown"}

        if threat_status is not None and threat_status not in valid_statuses:
            return { "success": False, "error": "Invalid threat_status value." }

        updated = False

        if threat_status is not None:
            self.domains[domain_name]["threat_status"] = threat_status
            updated = True

        if classification is not None:
            self.domains[domain_name]["classification"] = classification
            updated = True

        if updated:
            return { "success": True, "message": "Domain threat status and/or classification updated." }
        else:
            return { "success": False, "error": "No changes applied." }


    def reclassify_email_address_status(
        self,
        mail_address: str,
        threat_status: Optional[str] = None,
        classification: Optional[str] = None
    ) -> dict:
        """
        Change the threat_status and/or classification for an existing email address entry.

        Args:
            mail_address (str): Unique identifier for the email address entity.
            threat_status (Optional[str]): The new threat status ("malicious", "safe", or "unknown").
            classification (Optional[str]): The new threat classification (e.g., "phishing", "scam").

        Returns:
            dict: Success or failure, with message or error reason.

        Constraints:
            - Operation only allowed if email address exists.
            - threat_status, if provided, must be one of "malicious", "safe", "unknown".
            - At least one of threat_status or classification must be provided.
            - detection_date is updated to now if any change is made.
        """
        allowed_statuses = {"malicious", "safe", "unknown"}
        if mail_address not in self.email_addresses:
            return {"success": False, "error": "Email address not found"}

        if threat_status is None and classification is None:
            return {"success": False, "error": "No new threat_status or classification provided"}

        entry = self.email_addresses[mail_address]
        updated = False

        # Validate and update threat_status if required
        if threat_status is not None:
            normalized_status = threat_status.strip().lower()
            if normalized_status not in allowed_statuses:
                return {"success": False, "error": f"Invalid threat_status '{threat_status}'"}
            if entry["threat_status"] != normalized_status:
                entry["threat_status"] = normalized_status
                updated = True

        # Update classification if required
        if classification is not None:
            if entry["classification"] != classification:
                entry["classification"] = classification
                updated = True

        if updated:
            entry["detection_date"] = datetime.utcnow().isoformat()
            self.email_addresses[mail_address] = entry
            return {"success": True, "message": f"Reclassified email address {mail_address}"}
        else:
            return {"success": True, "message": "No changes made to email address classification or status"}

    def reclassify_url_status(
        self,
        url: str,
        threat_status: str = None,
        classification: str = None
    ) -> dict:
        """
        Change the threat_status and/or classification for an existing URL entry.

        Args:
            url (str): Unique identifier for the URL entry.
            threat_status (Optional[str]): New threat status. Must be "malicious", "safe", or "unknown" if provided.
            classification (Optional[str]): New threat classification (e.g. "phishing", "scam"), if provided.

        Returns:
            dict: {
                "success": True,
                "message": "URL threat status and/or classification updated"
            } or {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - The URL entry must exist in the system.
            - threat_status, if given, must be "malicious", "safe", or "unknown".
            - At least one of threat_status or classification must be provided.
        """
        # Check existence
        if url not in self.urls:
            return { "success": False, "error": "URL not found in database" }
        if threat_status is None and classification is None:
            return { "success": False, "error": "No update parameters provided" }
        allowed_status = {"malicious", "safe", "unknown"}
        if threat_status is not None and threat_status not in allowed_status:
            return { "success": False, "error": "Invalid threat_status value" }

        # Update the entry
        url_info = self.urls[url]
        changed = False
        if threat_status is not None and url_info["threat_status"] != threat_status:
            url_info["threat_status"] = threat_status
            changed = True
        if classification is not None and url_info["classification"] != classification:
            url_info["classification"] = classification
            changed = True

        if not changed:
            return {"success": True, "message": "No changes made (values already set as requested)"}
        else:
            self.urls[url] = url_info
            return {"success": True, "message": "URL threat status and/or classification updated"}


class AntiPhishingThreatIntelligenceDatabase(BaseEnv):
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

    def check_domain_presence(self, **kwargs):
        return self._call_inner_tool('check_domain_presence', kwargs)

    def check_email_address_presence(self, **kwargs):
        return self._call_inner_tool('check_email_address_presence', kwargs)

    def check_url_presence(self, **kwargs):
        return self._call_inner_tool('check_url_presence', kwargs)

    def get_domain_threat_info(self, **kwargs):
        return self._call_inner_tool('get_domain_threat_info', kwargs)

    def get_email_address_threat_info(self, **kwargs):
        return self._call_inner_tool('get_email_address_threat_info', kwargs)

    def get_url_threat_info(self, **kwargs):
        return self._call_inner_tool('get_url_threat_info', kwargs)

    def list_domains_by_threat_status(self, **kwargs):
        return self._call_inner_tool('list_domains_by_threat_status', kwargs)

    def list_email_addresses_by_threat_status(self, **kwargs):
        return self._call_inner_tool('list_email_addresses_by_threat_status', kwargs)

    def list_urls_by_threat_status(self, **kwargs):
        return self._call_inner_tool('list_urls_by_threat_status', kwargs)

    def list_all_domains(self, **kwargs):
        return self._call_inner_tool('list_all_domains', kwargs)

    def list_all_email_addresses(self, **kwargs):
        return self._call_inner_tool('list_all_email_addresses', kwargs)

    def list_all_urls(self, **kwargs):
        return self._call_inner_tool('list_all_urls', kwargs)

    def add_domain_entry(self, **kwargs):
        return self._call_inner_tool('add_domain_entry', kwargs)

    def add_email_address_entry(self, **kwargs):
        return self._call_inner_tool('add_email_address_entry', kwargs)

    def add_url_entry(self, **kwargs):
        return self._call_inner_tool('add_url_entry', kwargs)

    def update_domain_entry(self, **kwargs):
        return self._call_inner_tool('update_domain_entry', kwargs)

    def update_email_address_entry(self, **kwargs):
        return self._call_inner_tool('update_email_address_entry', kwargs)

    def update_url_entry(self, **kwargs):
        return self._call_inner_tool('update_url_entry', kwargs)

    def reclassify_domain_status(self, **kwargs):
        return self._call_inner_tool('reclassify_domain_status', kwargs)

    def reclassify_email_address_status(self, **kwargs):
        return self._call_inner_tool('reclassify_email_address_status', kwargs)

    def reclassify_url_status(self, **kwargs):
        return self._call_inner_tool('reclassify_url_status', kwargs)
