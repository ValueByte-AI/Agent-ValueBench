# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
from datetime import datetime
from typing import Optional, List, Dict
import re



class DomainNameInfo(TypedDict):
    domain_name: str
    status: str
    registration_date: str
    expiration_date: str
    owner_id: str

class OwnerInfo(TypedDict):
    owner_id: str
    name: str
    contact_info: str
    organization: str

class _GeneratedEnvImpl:
    def __init__(self):
        # DomainName: {domain_name: DomainNameInfo}
        self.domains: Dict[str, DomainNameInfo] = {}

        # Owner: {owner_id: OwnerInfo}
        self.owners: Dict[str, OwnerInfo] = {}

        # Constraints and invariants:
        # - Only domains with status = "registered" are 'active' for queries on registered domains
        # - Each domain_name is unique (domains dict key)
        # - Each domain_name must have exactly one owner (owner_id ref)
        # - Domain names must follow DNS permitted characters (see DNS specification)

    def _resolve_domain_key(self, domain_name: str) -> str | None:
        """
        Resolve a user-facing domain_name to the underlying dictionary key.

        Most cases store domains keyed directly by domain_name, but some older
        initial states use internal aliases while exposing the real domain_name
        only inside the record payload. Tool calls should consistently operate
        on the public domain_name shown to the agent.
        """
        if domain_name in self.domains:
            return domain_name
        for key, info in self.domains.items():
            if info.get("domain_name") == domain_name:
                return key
        return None

    def get_domain_by_name(self, domain_name: str) -> dict:
        """
        Retrieve all administrative info for a given domain name.

        Args:
            domain_name (str): The domain name to look up.

        Returns:
            dict: 
                - On success: {"success": True, "data": DomainNameInfo}
                - On failure: {"success": False, "error": "Domain not found"}

        Constraints:
            - The domain_name must exist in the system (case-insensitive lookup NOT required).
        """
        domain_key = self._resolve_domain_key(domain_name)
        if domain_key is None:
            return { "success": False, "error": "Domain not found" }

        return { "success": True, "data": self.domains[domain_key] }

    def list_all_domains(self) -> dict:
        """
        List all domain names and their metadata in the registration database, regardless of domain status.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[DomainNameInfo]  # List of domain info (may be empty)
            }
        Constraints:
            - No filtering; domains of any status are included.
            - If there are no domains, the data list will be empty.
        """
        domain_list = list(self.domains.values())
        return { "success": True, "data": domain_list }

    def list_registered_domains(self) -> dict:
        """
        List all domains currently registered (status == "registered").

        Returns:
            dict: {
                "success": True,
                "data": List[DomainNameInfo]  # List of active (registered) domains; empty if none
            }

        Constraints:
            - Only domains with status = "registered" are included.
        """
        result = [
            domain_info
            for domain_info in self.domains.values()
            if domain_info["status"] == "registered"
        ]
        return { "success": True, "data": result }

    def search_domains_by_substring(self, substring: str) -> dict:
        """
        Retrieve domains whose names contain a given substring (case-insensitive).

        Args:
            substring (str): The substring to match within domain names.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": List[DomainNameInfo],  # All domains containing the substring
                    }
                If no domains match, returns an empty data list.

        Constraints:
            - Search is case-insensitive.
            - All domains, regardless of status, are considered.
            - No error is returned for empty substrings.
        """
        substring = substring.lower()
        result = [
            domain_info for domain_info in self.domains.values()
            if substring in domain_info["domain_name"].lower()
        ]
        return { "success": True, "data": result }

    def count_registered_domains_by_substring(self, substring: str) -> dict:
        """
        Count the number of domains whose names contain the given substring and are currently registered.

        Args:
            substring (str): The substring to search for within domain names. Case-insensitive match.

        Returns:
            dict:
                {
                    "success": True,
                    "data": int  # count of matching registered domains
                }
                or
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - Only domains with status == "registered" are considered.
            - Substring matching is case-insensitive.
            - If substring is empty, returns the count of all registered domains.
        """
        if not isinstance(substring, str):
            return {"success": False, "error": "Provided substring must be a string"}
    
        substring_lower = substring.lower()
        count = sum(
            1
            for domain in self.domains.values()
            if domain["status"] == "registered"
            and substring_lower in domain["domain_name"].lower()
        )
        return {"success": True, "data": count}

    def get_domains_by_owner_id(self, owner_id: str) -> dict:
        """
        Retrieve all domain registrations associated with the given owner_id.

        Args:
            owner_id (str): The unique identifier of the owner.

        Returns:
            dict: {
                "success": True,
                "data": List[DomainNameInfo],  # List of all domain name records for this owner (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # e.g. "Owner not found"
            }

        Constraints:
            - The owner_id must exist in the database.
            - No filtering on 'status'; all domains for that owner are returned.
        """
        if owner_id not in self.owners:
            return { "success": False, "error": "Owner not found" }

        domain_list = [
            domain_info for domain_info in self.domains.values()
            if domain_info["owner_id"] == owner_id
        ]
        return { "success": True, "data": domain_list }

    def get_owner_by_id(self, owner_id: str) -> dict:
        """
        Retrieve all information about an owner using their owner_id.

        Args:
            owner_id (str): The unique identifier of the owner.

        Returns:
            dict: {
                "success": True,
                "data": OwnerInfo  # Full info for the owner,
            }
            or
            {
                "success": False,
                "error": str  # E.g., "Owner not found"
            }

        Constraints:
            - owner_id must exist in the system.
        """
        owner_info = self.owners.get(owner_id)
        if not owner_info:
            return {"success": False, "error": "Owner not found"}
        return {"success": True, "data": owner_info}

    def search_owners_by_name(self, name_substring: str) -> dict:
        """
        Retrieve all owners whose names contain the specified substring (case-insensitive).

        Args:
            name_substring (str): The substring to search for in owner names.

        Returns:
            dict: 
                {"success": True, "data": List[OwnerInfo]}
                or
                {"success": False, "error": str}

        Constraints:
            - Substring must not be empty.
            - Search is case-insensitive.
        """
        if not isinstance(name_substring, str) or not name_substring.strip():
            return {"success": False, "error": "Name substring must be a non-empty string."}
    
        substring_lower = name_substring.strip().lower()
        matches = [
            owner_info
            for owner_info in self.owners.values()
            if substring_lower in owner_info["name"].lower()
        ]
        return {"success": True, "data": matches}


    def list_domains_expiring_before(
        self,
        date: str,
        status: Optional[str] = None
    ) -> dict:
        """
        List domains that are expiring before the given date, optionally filtering by status.

        Args:
            date (str): The cutoff date (ISO format: "YYYY-MM-DD").
            status (Optional[str]): If provided, only domains with this status will be returned.

        Returns:
            dict: {
                "success": True,
                "data": List[DomainNameInfo],  # List of domain info objects
            }
            OR
            {
                "success": False,
                "error": str  # Description of error, e.g. invalid date format
            }

        Constraints:
            - Dates are assumed to be in "YYYY-MM-DD" format.
            - If the date format is invalid, returns a failure.
            - If status is provided, only include domains with that status.
        """
        # Validate date format
        try:
            cutoff_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return { "success": False, "error": "Invalid date format. Required: YYYY-MM-DD" }

        results = []
        for domain in self.domains.values():
            # Parse expiration_date
            try:
                exp_date = datetime.strptime(domain["expiration_date"], "%Y-%m-%d")
            except Exception:
                continue  # Ignore domains with invalid expiration_date

            if exp_date < cutoff_date:
                if status is not None:
                    if domain["status"] != status:
                        continue
                results.append(domain)

        return { "success": True, "data": results }

    def get_domain_status(self, domain_name: str) -> dict:
        """
        Retrieve the registration status of the specified domain.

        Args:
            domain_name (str): The fully qualified domain name to look up.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": { "status": <status_str> }
                    }
                - On failure (domain not found):
                    {
                        "success": False,
                        "error": "Domain not found"
                    }

        Constraints:
            - The domain_name must exist in the database.
        """
        domain_key = self._resolve_domain_key(domain_name)
        domain = self.domains.get(domain_key) if domain_key is not None else None
        if not domain:
            return { "success": False, "error": "Domain not found" }
        return { "success": True, "data": { "status": domain["status"] } }

    def get_domain_registration_dates(self, domain_name: str) -> dict:
        """
        Retrieve the registration and expiration dates for a given domain name.

        Args:
            domain_name (str): The domain name to retrieve dates for.

        Returns:
            dict:
                - On success: {
                    "success": True,
                    "data": {
                        "registration_date": str,
                        "expiration_date": str
                    }
                }
                - On failure: {
                    "success": False,
                    "error": str  # Reason, e.g. domain does not exist
                }

        Constraints:
            - The domain_name must exist in the database.
        """
        domain_key = self._resolve_domain_key(domain_name)
        domain = self.domains.get(domain_key) if domain_key is not None else None
        if not domain:
            return { "success": False, "error": "Domain name does not exist" }
    
        return {
            "success": True,
            "data": {
                "registration_date": domain["registration_date"],
                "expiration_date": domain["expiration_date"]
            }
        }

    def add_domain(
        self,
        domain_name: str,
        registration_date: str,
        expiration_date: str,
        owner_id: str,
        status: str = "registered"
    ) -> dict:
        """
        Register a new domain after validating:
          - Uniqueness of domain_name.
          - Existence of owner_id.
          - domain_name only uses permitted DNS characters.

        Args:
            domain_name (str): The domain to register.
            registration_date (str): Registration date (ISO8601 or YYYY-MM-DD).
            expiration_date (str): Expiration date (ISO8601 or YYYY-MM-DD).
            owner_id (str): The owner's unique ID (must exist in system).
            status (str): Status of the domain, default 'registered'.

        Returns:
            dict: 
              - On success: { "success": True, "message": "Domain <domain_name> registered successfully." }
              - On error: { "success": False, "error": "reason" }
    
        Constraints:
            - domain_name must be unique.
            - domain_name must follow DNS permitted characters.
            - owner_id must exist and be associated with an owner.
            - All fields are mandatory.
        """
        # Check all fields present
        if not domain_name or not registration_date or not expiration_date or not owner_id:
            return {"success": False, "error": "All fields are required."}

        # Uniqueness check
        if domain_name in self.domains:
            return {"success": False, "error": "Domain name already exists."}
    
        # Owner check
        if owner_id not in self.owners:
            return {"success": False, "error": "Associated owner_id does not exist."}
    
        validation = self.validate_domain_name_characters(domain_name)
        if not validation.get("success"):
            return {"success": False, "error": validation["error"]}

        # Create domain info object
        domain_info: DomainNameInfo = {
            "domain_name": domain_name,
            "status": status,
            "registration_date": registration_date,
            "expiration_date": expiration_date,
            "owner_id": owner_id
        }
        self.domains[domain_name] = domain_info
    
        return {"success": True, "message": f"Domain {domain_name} registered successfully."}

    def update_domain_status(self, domain_name: str, new_status: str) -> dict:
        """
        Change the status of a domain (e.g., registered, expired, on-hold).

        Args:
            domain_name (str): The unique domain name to update.
            new_status (str): The new status to set.

        Returns:
            dict:
                On Success:
                    { "success": True, "message": "Domain status updated to '<new_status>' for '<domain_name>'." }
                On Failure:
                    { "success": False, "error": "<reason>" }

        Constraints:
            - The domain_name must exist in the system.
            - No restriction on status value per current rules.
        """
        domain_key = self._resolve_domain_key(domain_name)
        if domain_key is None:
            return { "success": False, "error": f"Domain '{domain_name}' does not exist." }

        self.domains[domain_key]["status"] = new_status
        return {
            "success": True,
            "message": f"Domain status updated to '{new_status}' for '{domain_name}'."
        }

    def update_domain_expiration(self, domain_name: str, new_expiration_date: str) -> dict:
        """
        Modify the expiration date of a domain.

        Args:
            domain_name (str): The domain whose expiration date is to be updated.
            new_expiration_date (str): The new expiration date (expected as string).

        Returns:
            dict:
                - On success: { "success": True, "message": "Expiration date updated for <domain_name>" }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - The domain_name must exist in the database.
            - The new_expiration_date should be a non-empty string.
        """
        domain_key = self._resolve_domain_key(domain_name)
        if domain_key is None:
            return { "success": False, "error": "Domain does not exist" }
        if not isinstance(new_expiration_date, str) or not new_expiration_date.strip():
            return { "success": False, "error": "Invalid expiration date format" }
        self.domains[domain_key]['expiration_date'] = new_expiration_date
        return {
            "success": True,
            "message": f"Expiration date updated for {domain_name}"
        }

    def transfer_domain_ownership(self, domain_name: str, new_owner_id: str) -> dict:
        """
        Assigns the specified domain to a new owner.

        Args:
            domain_name (str): The domain to transfer.
            new_owner_id (str): The owner_id of the new owner.

        Returns:
            dict: {
                "success": True,
                "message": "Domain ownership transferred to <new_owner_id> for <domain_name>."
            }
            or
            {
                "success": False,
                "error": "<error reason>"
            }

        Constraints:
            - domain_name must exist.
            - new_owner_id must exist.
            - The transfer should not be performed if the domain is already owned by new_owner_id.
        """
        # Check if the domain exists
        domain_key = self._resolve_domain_key(domain_name)
        if domain_key is None:
            return {"success": False, "error": "Domain does not exist."}

        # Check if the new owner exists
        if new_owner_id not in self.owners:
            return {"success": False, "error": "New owner does not exist."}

        # Check if domain is already owned by new_owner_id
        current_owner_id = self.domains[domain_key]["owner_id"]
        if current_owner_id == new_owner_id:
            return {"success": False, "error": "Domain is already owned by the specified new owner."}

        # Transfer ownership
        self.domains[domain_key]["owner_id"] = new_owner_id

        return {
            "success": True,
            "message": f"Domain ownership transferred to {new_owner_id} for {domain_name}."
        }

    def delete_domain(self, domain_name: str) -> dict:
        """
        Remove a domain from the system.
    
        Args:
            domain_name (str): The fully-qualified domain name to be deleted.
        
        Returns:
            dict: 
                If success: {"success": True, "message": "Domain <domain_name> deleted."}
                If fail: {"success": False, "error": <reason>}
    
        Constraints:
            - Domain must exist in the system.
            - Domain can only be deleted if status is NOT "registered".
        """
        domain_key = self._resolve_domain_key(domain_name)
        domain = self.domains.get(domain_key) if domain_key is not None else None
        if not domain:
            return {"success": False, "error": "Domain does not exist."}
        if domain["status"] == "registered":
            return {"success": False, "error": "Cannot delete an active registered domain."}

        del self.domains[domain_key]
        return {"success": True, "message": f"Domain '{domain_name}' deleted."}

    def add_owner(self, owner_id: str, name: str, contact_info: str, organization: str) -> dict:
        """
        Add a new owner record to the database.

        Args:
            owner_id (str): Unique owner identifier.
            name (str): Name of the owner.
            contact_info (str): Owner's contact information.
            organization (str): Owner's organization.

        Returns:
            dict: {
                "success": True,
                "message": "Owner added successfully"
            }
            or
            {
                "success": False,
                "error": str  # Error description, e.g. owner_id already exists
            }

        Constraints:
            - owner_id must be unique in the database.
        """
        if owner_id in self.owners:
            return { "success": False, "error": "Owner ID already exists" }

        owner_info = {
            "owner_id": owner_id,
            "name": name,
            "contact_info": contact_info,
            "organization": organization,
        }
        self.owners[owner_id] = owner_info

        return { "success": True, "message": "Owner added successfully" }

    def update_owner_info(self, owner_id: str, contact_info: str = None, organization: str = None) -> dict:
        """
        Update the contact information and/or organization of a domain owner.

        Args:
            owner_id (str): Unique identifier for the owner to be updated.
            contact_info (str, optional): New contact info (email, phone, etc.).
            organization (str, optional): New organization name.

        Returns:
            dict:
                - On success: { "success": True, "message": "Owner info updated successfully." }
                - On failure: { "success": False, "error": <error message> }

        Constraints:
            - The owner must exist (owner_id in self.owners).
            - At least one attribute (contact_info, organization) must be provided.
        """
        if owner_id not in self.owners:
            return { "success": False, "error": "Owner with given owner_id does not exist." }

        if contact_info is None and organization is None:
            return { "success": False, "error": "No update parameters provided. Specify contact_info and/or organization." }

        owner = self.owners[owner_id]
        if contact_info is not None:
            owner["contact_info"] = contact_info
        if organization is not None:
            owner["organization"] = organization

        return { "success": True, "message": "Owner info updated successfully." }

    def validate_domain_name_characters(self, domain_name: str) -> dict:
        """
        Check if a domain name contains only DNS-permitted characters.

        Args:
            domain_name (str): The domain name to validate.

        Returns:
            dict: {
                "success": True,
                "message": "Domain name is valid."
            }
            or
            {
                "success": False,
                "error": "Description of the validation failure."
            }

        Constraints (according to DNS rules):
            - Only a-z, A-Z, 0-9, hyphen '-', and dot '.' permitted.
            - Each label (parts between dots) must not start or end with hyphen and be 1-63 chars.
            - Total length must not exceed 253 chars.
            - Empty string, trailing dots, or consecutive dots are invalid.
        """
        if not isinstance(domain_name, str) or not domain_name:
            return {"success": False, "error": "Domain name must be a non-empty string."}

        if len(domain_name) > 253:
            return {"success": False, "error": "Domain name exceeds 253 characters."}

        # No leading/trailing dot, no consecutive dots
        if domain_name.startswith(".") or domain_name.endswith("."):
            return {"success": False, "error": "Domain name cannot start or end with a dot."}
        if ".." in domain_name:
            return {"success": False, "error": "Domain name cannot contain consecutive dots."}
    
        # Only ASCII alphanum, dashes, dots
        if not re.fullmatch(r"[A-Za-z0-9\-.]+", domain_name):
            return {"success": False, "error": "Domain name contains invalid characters."}

        labels = domain_name.split(".")
        for label in labels:
            label_len = len(label)
            if label_len == 0:
                return {"success": False, "error": "Domain name has empty label."}
            if label_len > 63:
                return {"success": False, "error": f"Label '{label}' exceeds 63 characters."}
            if label.startswith("-") or label.endswith("-"):
                return {"success": False, "error": f"Label '{label}' must not start or end with a hyphen."}

        return {"success": True, "message": "Domain name is valid."}

    def renew_domain(self, domain_name: str, new_expiration_date: str) -> dict:
        """
        Extend the expiration date of the specified domain and update status if applicable.

        Args:
            domain_name (str): The domain name to renew.
            new_expiration_date (str): The new expiration date (format: "YYYY-MM-DD").

        Returns:
            dict:
                success: True/False
                message: Success description (on success)
                error: Failure reason (on failure)

        Constraints:
            - domain_name must exist in the database.
            - domain_name must contain only permitted DNS characters.
            - new_expiration_date should extend the previous expiration.
            - If the domain was expired and renewal brings it 'active', status should be set to 'registered'.
        """
        domain_key = self._resolve_domain_key(domain_name)
        domain = self.domains.get(domain_key) if domain_key is not None else None
        if not domain:
            return { "success": False, "error": "Domain not found" }

        validation = self.validate_domain_name_characters(domain_name)
        if not validation.get("success"):
            return { "success": False, "error": validation["error"] }

        old_expiration = domain["expiration_date"]
        # Check if new_expiration_date extends old_expiration
        try:
            old_dt = datetime.strptime(old_expiration, "%Y-%m-%d")
            new_dt = datetime.strptime(new_expiration_date, "%Y-%m-%d")
        except Exception:
            return { "success": False, "error": "Invalid date format; expected YYYY-MM-DD" }

        if new_dt <= old_dt:
            return { "success": False, "error": "New expiration date must be later than current expiration" }

        # Update expiration
        domain["expiration_date"] = new_expiration_date

        # Renewal that extends the domain should reactivate suspended/expired registrations.
        if domain["status"] != "registered":
            domain["status"] = "registered"

        self.domains[domain_key] = domain  # Save back

        return {
            "success": True,
            "message": f"Domain '{domain_name}' renewed to expiration date {new_expiration_date}."
        }


class DomainNameRegistrationDatabase(BaseEnv):
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

    def get_domain_by_name(self, **kwargs):
        return self._call_inner_tool('get_domain_by_name', kwargs)

    def list_all_domains(self, **kwargs):
        return self._call_inner_tool('list_all_domains', kwargs)

    def list_registered_domains(self, **kwargs):
        return self._call_inner_tool('list_registered_domains', kwargs)

    def search_domains_by_substring(self, **kwargs):
        return self._call_inner_tool('search_domains_by_substring', kwargs)

    def count_registered_domains_by_substring(self, **kwargs):
        return self._call_inner_tool('count_registered_domains_by_substring', kwargs)

    def get_domains_by_owner_id(self, **kwargs):
        return self._call_inner_tool('get_domains_by_owner_id', kwargs)

    def get_owner_by_id(self, **kwargs):
        return self._call_inner_tool('get_owner_by_id', kwargs)

    def search_owners_by_name(self, **kwargs):
        return self._call_inner_tool('search_owners_by_name', kwargs)

    def list_domains_expiring_before(self, **kwargs):
        return self._call_inner_tool('list_domains_expiring_before', kwargs)

    def get_domain_status(self, **kwargs):
        return self._call_inner_tool('get_domain_status', kwargs)

    def get_domain_registration_dates(self, **kwargs):
        return self._call_inner_tool('get_domain_registration_dates', kwargs)

    def add_domain(self, **kwargs):
        return self._call_inner_tool('add_domain', kwargs)

    def update_domain_status(self, **kwargs):
        return self._call_inner_tool('update_domain_status', kwargs)

    def update_domain_expiration(self, **kwargs):
        return self._call_inner_tool('update_domain_expiration', kwargs)

    def transfer_domain_ownership(self, **kwargs):
        return self._call_inner_tool('transfer_domain_ownership', kwargs)

    def delete_domain(self, **kwargs):
        return self._call_inner_tool('delete_domain', kwargs)

    def add_owner(self, **kwargs):
        return self._call_inner_tool('add_owner', kwargs)

    def update_owner_info(self, **kwargs):
        return self._call_inner_tool('update_owner_info', kwargs)

    def validate_domain_name_characters(self, **kwargs):
        return self._call_inner_tool('validate_domain_name_characters', kwargs)

    def renew_domain(self, **kwargs):
        return self._call_inner_tool('renew_domain', kwargs)
