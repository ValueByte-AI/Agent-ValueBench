# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, Optional, TypedDict



class DomainInfo(TypedDict):
    domain_id: str
    domain_name: str
    organization_name: str
    category: str

class TechnologyInfo(TypedDict):
    technology_id: str
    technology_name: str
    type: str
    category: str

class DomainTechnologyMappingInfo(TypedDict, total=False):
    domain_id: str
    technology_id: str
    detection_date: Optional[str]          # Optional; could also be float (timestamp)
    detection_method: Optional[str]        # Optional
    confidence_score: Optional[float]      # Optional

class _GeneratedEnvImpl:
    def __init__(self):
        # Domains: {domain_id: DomainInfo}
        self.domains: Dict[str, DomainInfo] = {}

        # Technologies: {technology_id: TechnologyInfo}
        self.technologies: Dict[str, TechnologyInfo] = {}

        # Mappings: List of DomainTechnologyMappingInfo
        self.domain_technology_mappings: List[DomainTechnologyMappingInfo] = []

        # Constraints:
        # - A domain can be mapped to zero or more technologies.
        # - A technology can be mapped to zero or more domains.
        # - Technology entries should be unique in the technology registry.
        # - A mapping must reference valid (existing) domain and technology entries.
        # - Detections may include optional metadata (method, score, or last detection date); core is existence of mapping.

    def get_domain_by_name(self, domain_name: str) -> dict:
        """
        Retrieve the information of a domain given its domain_name.

        Args:
            domain_name (str): The domain name to search for.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": DomainInfo
                    }
                On failure (not found):
                    {
                        "success": False,
                        "error": "Domain not found"
                    }

        Constraints:
            - The domain_name must match exactly (case-sensitive).
            - If multiple domains have the same name, returns the first matched.
        """
        for domain in self.domains.values():
            if domain["domain_name"] == domain_name:
                return {"success": True, "data": domain}
        return {"success": False, "error": "Domain not found"}

    def get_domain_by_id(self, domain_id: str) -> dict:
        """
        Retrieve the information of a domain given its domain_id.

        Args:
            domain_id (str): Unique identifier for the domain.

        Returns:
            dict: {
                "success": True,
                "data": DomainInfo
            }
            or
            {
                "success": False,
                "error": "Domain ID not found"
            }

        Constraints:
            - The domain_id must exist in the database.
        """
        if domain_id not in self.domains:
            return { "success": False, "error": "Domain ID not found" }

        domain_info = self.domains[domain_id]
        return { "success": True, "data": domain_info }

    def list_all_domains(self) -> dict:
        """
        Retrieve the full list of registered domains.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[DomainInfo]  # All registered domain information (may be empty)
            }
        """
        return {
            "success": True,
            "data": list(self.domains.values())
        }

    def get_technology_by_name(self, technology_name: str) -> dict:
        """
        Retrieve information of a technology given its technology_name.

        Args:
            technology_name (str): The name of the technology to retrieve.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": TechnologyInfo  # Technology info dict if found
                }
                OR
                {
                    "success": False,
                    "error": str  # "Technology not found"
                }

        Constraints:
            - Technology entries are unique by technology_name.
        """
        for tech in self.technologies.values():
            if tech["technology_name"] == technology_name:
                return { "success": True, "data": tech }
        return { "success": False, "error": "Technology not found" }

    def get_technology_by_id(self, technology_id: str) -> dict:
        """
        Retrieve the information of a technology given its technology_id.

        Args:
            technology_id (str): The unique identifier of the technology.

        Returns:
            dict: 
                - On success: { "success": True, "data": TechnologyInfo }
                - On failure: { "success": False, "error": "Technology not found" }

        Constraints:
            - Technology must exist in the technology registry.
        """
        if not technology_id or technology_id not in self.technologies:
            return { "success": False, "error": "Technology not found" }
        technology_info = self.technologies[technology_id]
        return { "success": True, "data": technology_info }

    def list_all_technologies(self) -> dict:
        """
        Retrieve the full list of registered technologies.

        Returns:
            dict:
                - success (bool): Whether the operation succeeded.
                - data (List[TechnologyInfo]): List of all technologies (empty if none are registered).
        """
        technologies = list(self.technologies.values())
        return { "success": True, "data": technologies }

    def list_domains_by_technology_name(self, technology_name: str) -> dict:
        """
        Retrieve all domains (DomainInfo) using the specified technology, identified by its technology_name.

        Args:
            technology_name (str): The name of the technology to search.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[DomainInfo]  # All domains using the given technology
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # "Technology not found"
                    }

        Constraints:
            - Technology name must exist in the registry.
            - Only domains with valid entries are returned.
        """
        # Find technology_id by technology name
        tech_id = None
        for t in self.technologies.values():
            if t["technology_name"] == technology_name:
                tech_id = t["technology_id"]
                break

        if tech_id is None:
            return {"success": False, "error": "Technology not found"}

        # Find mappings for this technology_id
        domain_ids = [
            m["domain_id"]
            for m in self.domain_technology_mappings
            if m.get("technology_id") == tech_id
        ]

        # Accumulate unique DomainInfo entries
        results = []
        seen = set()
        for domain_id in domain_ids:
            if domain_id in self.domains and domain_id not in seen:
                results.append(self.domains[domain_id])
                seen.add(domain_id)

        return {"success": True, "data": results}

    def list_domains_by_technology_id(self, technology_id: str) -> dict:
        """
        Retrieve all domains using the specified technology (by technology_id).

        Args:
            technology_id (str): The unique identifier for the technology.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": List[DomainInfo],  # List of domains using the given technology (may be empty)
                }
                or
                {
                    "success": False,
                    "error": str  # Description of the error, e.g. technology ID does not exist
                }
        Constraints:
            - The technology_id must exist in the registry.
            - Only domains that still exist are returned.
            - Duplicates are not returned.
        """
        if technology_id not in self.technologies:
            return { "success": False, "error": "Technology ID does not exist" }

        # Find all unique domain_ids mapped to the given technology_id
        domain_ids = set(
            mapping["domain_id"]
            for mapping in self.domain_technology_mappings
            if mapping.get("technology_id") == technology_id
        )

        # Build result list of domains that still exist
        domains = [
            self.domains[domain_id]
            for domain_id in domain_ids
            if domain_id in self.domains
        ]

        return { "success": True, "data": domains }

    def list_technologies_by_domain_name(self, domain_name: str) -> dict:
        """
        Retrieve all technologies detected on the specified domain, referenced by domain_name.

        Args:
            domain_name (str): The domain name to look up technologies for.

        Returns:
            dict: {
                "success": True,
                "data": List[TechnologyInfo]  # Full info for each technology detected on the domain
            }
            or
            {
                "success": False,
                "error": str  # "Domain not found"
            }

        Constraints:
            - The given domain_name must exist in the database.
            - Only mappings where both the domain and technology exist are considered.

        Notes:
            - Returns an empty list if domain is valid but no technologies are mapped.
        """
        # Find the domain_id from domain_name
        domain_id = None
        for dom in self.domains.values():
            if dom["domain_name"] == domain_name:
                domain_id = dom["domain_id"]
                break

        if domain_id is None:
            return {"success": False, "error": "Domain not found"}

        # Find all technology_ids mapped to this domain
        tech_ids = set()
        for mapping in self.domain_technology_mappings:
            if mapping.get("domain_id") == domain_id:
                tech_ids.add(mapping.get("technology_id"))

        # Retrieve TechnologyInfo for each technology_id
        tech_list = []
        for tech_id in tech_ids:
            tech_info = self.technologies.get(tech_id)
            if tech_info:
                tech_list.append(tech_info)

        return {"success": True, "data": tech_list}

    def list_technologies_by_domain_id(self, domain_id: str) -> dict:
        """
        Retrieve all technologies (with metadata) detected for the specified domain by domain_id.

        Args:
            domain_id (str): The ID of the domain to search for.

        Returns:
            dict: {
                "success": True,
                "data": List[TechnologyInfo]  # May be empty if no mappings
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - domain_id must exist in the database.
            - Only technologies present in the registry will be returned.
        """
        if domain_id not in self.domains:
            return { "success": False, "error": "Domain not found" }

        # Collect all technology_ids mapped to this domain
        tech_ids = [
            mapping["technology_id"]
            for mapping in self.domain_technology_mappings
            if mapping.get("domain_id") == domain_id
        ]

        # Build TechnologyInfo list (skip if tech_id not present in registry)
        technologies = [
            self.technologies[tid]
            for tid in tech_ids
            if tid in self.technologies
        ]

        return { "success": True, "data": technologies }

    def get_domain_technology_mapping(self, domain_id: str, technology_id: str) -> dict:
        """
        Retrieve all mapping record(s), including metadata, for a given (domain, technology) pair.

        Args:
            domain_id (str): The ID of the domain.
            technology_id (str): The ID of the technology.

        Returns:
            dict:
              - If domain_id or technology_id do not refer to an existing entry:
                    { "success": False, "error": "Domain does not exist" } or
                    { "success": False, "error": "Technology does not exist" }
              - If IDs exist, returns:
                    { "success": True, "data": List[DomainTechnologyMappingInfo] }
                    (Possibly an empty list if there are currently no mappings.)

        Constraints:
            - domain_id and technology_id must refer to existing entries in the database.
            - Returns all mappings between the given domain and technology, including metadata.
        """
        if domain_id not in self.domains:
            return { "success": False, "error": "Domain does not exist" }
        if technology_id not in self.technologies:
            return { "success": False, "error": "Technology does not exist" }

        mappings = [
            mapping for mapping in self.domain_technology_mappings
            if mapping.get("domain_id") == domain_id and mapping.get("technology_id") == technology_id
        ]
        return { "success": True, "data": mappings }

    def list_mappings_for_domain(self, domain_id: str) -> dict:
        """
        List all mapping records (with metadata) for the specified domain.

        Args:
            domain_id (str): Unique identifier of the domain.

        Returns:
            dict:
                success (bool): Operation successful or not.
                data (List[DomainTechnologyMappingInfo]): List of mapping records (can be empty).
                OR
                error (str): Error message if failure.

        Constraints:
            - domain_id must exist in the domains registry.
        """
        if domain_id not in self.domains:
            return {"success": False, "error": "Domain does not exist"}

        mappings = [
            m for m in self.domain_technology_mappings
            if m.get("domain_id") == domain_id
        ]
        return {"success": True, "data": mappings}

    def list_mappings_for_technology(self, technology_id: str) -> dict:
        """
        List all domain-technology mapping records (with metadata) for a given technology.

        Args:
            technology_id (str): The unique ID of the technology.

        Returns:
            dict: {
                "success": True,
                "data": List[DomainTechnologyMappingInfo]  # all mappings involving this technology
            }
            or
            {
                "success": False,
                "error": str  # Error message, e.g., technology not found
            }

        Constraints:
            - The technology_id must exist in the technology registry.
        """
        if technology_id not in self.technologies:
            return { "success": False, "error": "Technology not found" }

        mappings = [
            mapping
            for mapping in self.domain_technology_mappings
            if mapping.get("technology_id") == technology_id
        ]

        return { "success": True, "data": mappings }

    def check_mapping_exists(self, domain_id: str, technology_id: str) -> dict:
        """
        Check whether a mapping exists between a given domain and technology.

        Args:
            domain_id (str): ID of the domain to check.
            technology_id (str): ID of the technology to check.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": bool,  # True if mapping exists, False otherwise
                    }
                On error:
                    {
                        "success": False,
                        "error": str,  # Reason for failure (domain or technology does not exist)
                    }

        Constraints:
            - Both domain_id and technology_id must exist in their respective registries.
        """
        if domain_id not in self.domains:
            return {"success": False, "error": "Domain does not exist."}
        if technology_id not in self.technologies:
            return {"success": False, "error": "Technology does not exist."}
    
        exists = any(
            (m.get("domain_id") == domain_id and m.get("technology_id") == technology_id)
            for m in self.domain_technology_mappings
        )
        return {"success": True, "data": exists}

    def get_mapping_metadata(self, domain_id: str, technology_id: str) -> dict:
        """
        Retrieve mapping metadata (detection_date, detection_method, confidence_score)
        for the specified (domain_id, technology_id) pair.

        Args:
            domain_id (str): The ID of the domain.
            technology_id (str): The ID of the technology.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "detection_date": Optional[str],
                    "detection_method": Optional[str],
                    "confidence_score": Optional[float],
                }
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The domain_id and technology_id must exist.
            - The mapping must exist between domain and technology.
            - If metadata fields are missing, their values will be None.
        """
        if domain_id not in self.domains:
            return { "success": False, "error": "Domain ID does not exist" }

        if technology_id not in self.technologies:
            return { "success": False, "error": "Technology ID does not exist" }

        for mapping in self.domain_technology_mappings:
            if mapping.get("domain_id") == domain_id and mapping.get("technology_id") == technology_id:
                data = {
                    "detection_date": mapping.get("detection_date"),
                    "detection_method": mapping.get("detection_method"),
                    "confidence_score": mapping.get("confidence_score"),
                }
                return { "success": True, "data": data }

        return { "success": False, "error": "Mapping does not exist for the specified domain and technology" }

    def add_domain(
        self,
        domain_id: str,
        domain_name: str,
        organization_name: str,
        category: str
    ) -> dict:
        """
        Add a new domain to the database.

        Args:
            domain_id (str): Unique ID for the new domain.
            domain_name (str): The domain name (e.g., example.com).
            organization_name (str): Name of the owning organization.
            category (str): Domain category (e.g., 'E-commerce').

        Returns:
            dict: 
                - On success: { "success": True, "message": "Domain added successfully." }
                - On error:  { "success": False, "error": <reason> }

        Constraints:
            - domain_id must be unique (cannot already exist).
            - All fields are required and must be non-empty.
        """

        if not all([domain_id, domain_name, organization_name, category]):
            return { "success": False, "error": "All fields must be provided and non-empty." }

        if domain_id in self.domains:
            return { "success": False, "error": "Domain ID already exists." }

        new_domain = {
            "domain_id": domain_id,
            "domain_name": domain_name,
            "organization_name": organization_name,
            "category": category,
        }

        self.domains[domain_id] = new_domain
        return { "success": True, "message": "Domain added successfully." }

    def remove_domain(self, domain_id: str) -> dict:
        """
        Remove a domain and all its associated technology mappings from the database.

        Args:
            domain_id (str): The unique ID of the domain to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Domain <domain_id> and all its mappings were removed."
            }
            or
            {
                "success": False,
                "error": "Domain not found."
            }

        Constraints:
            - The domain must exist; otherwise, return an error.
            - All mappings involving this domain will be removed.
        """
        if domain_id not in self.domains:
            return {"success": False, "error": "Domain not found."}

        # Remove the domain entry
        del self.domains[domain_id]

        # Remove all mappings with this domain_id
        prev_count = len(self.domain_technology_mappings)
        self.domain_technology_mappings = [
            mapping for mapping in self.domain_technology_mappings
            if mapping.get("domain_id") != domain_id
        ]
        removed_mappings = prev_count - len(self.domain_technology_mappings)

        return {
            "success": True,
            "message": f"Domain {domain_id} and all its mappings were removed."
        }

    def update_domain_info(
        self,
        domain_id: str,
        domain_name: str = None,
        organization_name: str = None,
        category: str = None
    ) -> dict:
        """
        Modify the attributes of an existing domain.

        Args:
            domain_id (str): The unique identifier of the domain to update.
            domain_name (str, optional): New domain name.
            organization_name (str, optional): New organization name.
            category (str, optional): New category.

        Returns:
            dict:
                On success: {"success": True, "message": "Domain info updated successfully."}
                On failure: {"success": False, "error": "<reason>"}

        Constraints:
            - The given domain_id must exist.
            - Only domain_name, organization_name, and category may be updated.
            - No change to domain_id is allowed.
        """
        if domain_id not in self.domains:
            return { "success": False, "error": "Domain does not exist." }
    
        updated = False
        domain_info = self.domains[domain_id]

        # Only update if a field is explicitly supplied (not None)
        if domain_name is not None:
            domain_info["domain_name"] = domain_name
            updated = True
        if organization_name is not None:
            domain_info["organization_name"] = organization_name
            updated = True
        if category is not None:
            domain_info["category"] = category
            updated = True

        if updated:
            self.domains[domain_id] = domain_info
            return { "success": True, "message": "Domain info updated successfully." }
        else:
            return { "success": True, "message": "No changes made to domain info." }

    def add_technology(
        self,
        technology_id: str,
        technology_name: str,
        type: str,
        category: str
    ) -> dict:
        """
        Add a new technology to the registry.

        Args:
            technology_id (str): Unique identifier for the technology.
            technology_name (str): Human-readable name of the technology.
            type (str): The type (e.g., 'SaaS', 'Library', etc.).
            category (str): Category of the technology.

        Returns:
            dict: {
                "success": True,
                "message": "Technology <technology_id> added."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - Technology entries must be unique by technology_id.
        """
        if not technology_id or not technology_name or not type or not category:
            return { "success": False, "error": "All fields (id, name, type, category) are required." }
        if technology_id in self.technologies:
            return { "success": False, "error": f"Technology {technology_id} already exists." }

        self.technologies[technology_id] = {
            "technology_id": technology_id,
            "technology_name": technology_name,
            "type": type,
            "category": category
        }
        return { "success": True, "message": f"Technology {technology_id} added." }

    def remove_technology(self, technology_id: str) -> dict:
        """
        Remove a technology and all its associated domain mappings from the database.

        Args:
            technology_id (str): The ID of the technology to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Technology and its mappings removed."
            }
            or
            {
                "success": False,
                "error": "Technology does not exist."
            }

        Constraints:
            - The technology must exist in the technology registry.
            - All domain-technology mappings referencing this technology will be removed.
        """
        if technology_id not in self.technologies:
            return {"success": False, "error": "Technology does not exist."}

        # Remove the technology itself
        del self.technologies[technology_id]

        # Remove all mappings that include this technology
        original_count = len(self.domain_technology_mappings)
        self.domain_technology_mappings = [
            m for m in self.domain_technology_mappings
            if m.get("technology_id") != technology_id
        ]
        removed_count = original_count - len(self.domain_technology_mappings)

        return {
            "success": True,
            "message": f"Technology and its {removed_count} mapping(s) removed."
        }

    def update_technology_info(
        self, 
        technology_id: str, 
        technology_name: str = None,
        type: str = None,
        category: str = None
    ) -> dict:
        """
        Modify the attributes of an existing technology entry.

        Args:
            technology_id (str): The unique ID of the technology to modify.
            technology_name (str, optional): New name for the technology.
            type (str, optional): New type for the technology.
            category (str, optional): New category for the technology.

        Returns:
            dict: {
                "success": True,
                "message": "Technology info updated."
            }
            or
            {
                "success": False,
                "error": str  # Description of the error
            }

        Constraints:
            - technology_id must exist in the registry.
            - If technology_name is changed, it must remain unique in the technology registry.
            - At least one updatable field should be provided.
        """
        if technology_id not in self.technologies:
            return {"success": False, "error": "Technology not found."}

        # Collect fields to update
        fields_to_update = {}
        if technology_name is not None:
            # Check for name uniqueness if it is changing
            for tid, tinfo in self.technologies.items():
                if tid != technology_id and tinfo["technology_name"] == technology_name:
                    return {"success": False, "error": "Technology name already exists."}
            fields_to_update["technology_name"] = technology_name
        if type is not None:
            fields_to_update["type"] = type
        if category is not None:
            fields_to_update["category"] = category

        if not fields_to_update:
            return {"success": False, "error": "No update fields provided."}

        # Perform update
        self.technologies[technology_id].update(fields_to_update)

        return {"success": True, "message": "Technology info updated."}

    def add_domain_technology_mapping(
        self,
        domain_id: str,
        technology_id: str,
        detection_date: Optional[str] = None,
        detection_method: Optional[str] = None,
        confidence_score: Optional[float] = None
    ) -> dict:
        """
        Add a mapping between a domain and a technology with optional metadata.
        Ensures both referenced entries exist and mapping does not already exist.

        Args:
            domain_id (str): The ID of the domain.
            technology_id (str): The ID of the technology.
            detection_date (Optional[str]): The detection date (string or ISO format).
            detection_method (Optional[str]): The method used for detection.
            confidence_score (Optional[float]): Confidence score of mapping.

        Returns:
            dict: {
                "success": True,
                "message": "Mapping added between domain {domain_id} and technology {technology_id}."
            }
            or
            dict: {
                "success": False,
                "error": "Reason for failure"
            }

        Constraints:
            - The domain_id and technology_id must reference existing records.
            - The (domain_id, technology_id) mapping must not already exist.
        """
        if domain_id not in self.domains:
            return { "success": False, "error": "Domain does not exist." }
        if technology_id not in self.technologies:
            return { "success": False, "error": "Technology does not exist." }

        # Enforce uniqueness of mapping between domain_id and technology_id
        for mapping in self.domain_technology_mappings:
            if mapping.get("domain_id") == domain_id and mapping.get("technology_id") == technology_id:
                return { "success": False, "error": "Mapping already exists." }

        mapping: DomainTechnologyMappingInfo = {
            "domain_id": domain_id,
            "technology_id": technology_id
        }
        if detection_date is not None:
            mapping["detection_date"] = detection_date
        if detection_method is not None:
            mapping["detection_method"] = detection_method
        if confidence_score is not None:
            mapping["confidence_score"] = confidence_score

        self.domain_technology_mappings.append(mapping)

        return {
            "success": True,
            "message": f"Mapping added between domain {domain_id} and technology {technology_id}."
        }

    def remove_domain_technology_mapping(self, domain_id: str, technology_id: str) -> dict:
        """
        Remove all mappings between a domain (by domain_id) and a technology (by technology_id).

        Args:
            domain_id (str): The domain's unique identifier.
            technology_id (str): The technology's unique identifier.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "message": "Mapping between domain_id X and technology_id Y removed."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "reason"
                    }

        Constraints:
          - The mapping to remove must exist.
          - The domain and technology must exist.
          - All mappings matching this domain_id and technology_id are removed.
        """
        if domain_id not in self.domains:
            return {"success": False, "error": "Domain ID does not exist."}
        if technology_id not in self.technologies:
            return {"success": False, "error": "Technology ID does not exist."}

        # Find and remove mappings
        initial_count = len(self.domain_technology_mappings)
        self.domain_technology_mappings = [
            mapping for mapping in self.domain_technology_mappings
            if not (mapping.get("domain_id") == domain_id and mapping.get("technology_id") == technology_id)
        ]
        removed_count = initial_count - len(self.domain_technology_mappings)
        if removed_count == 0:
            return {"success": False, "error": "Mapping between this domain and technology does not exist."}

        return {
            "success": True,
            "message": f"Mapping between domain_id {domain_id} and technology_id {technology_id} removed."
        }

    def update_mapping_metadata(
        self, 
        domain_id: str,
        technology_id: str,
        detection_date: Optional[str] = None,
        detection_method: Optional[str] = None,
        confidence_score: Optional[float] = None
    ) -> dict:
        """
        Update the detection metadata (detection_date, detection_method, confidence_score)
        for the mapping between a given domain and technology.

        Args:
            domain_id (str): The domain's unique ID.
            technology_id (str): The technology's unique ID.
            detection_date (Optional[str]): New detection date (optional).
            detection_method (Optional[str]): New detection method (optional).
            confidence_score (Optional[float]): New detection confidence score (optional).

        Returns:
            dict:
                On success: { "success": True, "message": "Mapping metadata updated successfully." }
                On error:   { "success": False, "error": <reason> }

        Constraints:
            - The mapping between specified domain and technology must exist.
            - Only provided fields are updated; others remain unchanged.
        """
        found = False
        for mapping in self.domain_technology_mappings:
            if mapping.get("domain_id") == domain_id and mapping.get("technology_id") == technology_id:
                found = True
                if detection_date is not None:
                    mapping["detection_date"] = detection_date
                if detection_method is not None:
                    mapping["detection_method"] = detection_method
                if confidence_score is not None:
                    mapping["confidence_score"] = confidence_score
                break

        if not found:
            return { "success": False, "error": "Domain-technology mapping does not exist." }

        return { "success": True, "message": "Mapping metadata updated successfully." }


class TechnologyProfilingDatabase(BaseEnv):
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

    def get_domain_by_id(self, **kwargs):
        return self._call_inner_tool('get_domain_by_id', kwargs)

    def list_all_domains(self, **kwargs):
        return self._call_inner_tool('list_all_domains', kwargs)

    def get_technology_by_name(self, **kwargs):
        return self._call_inner_tool('get_technology_by_name', kwargs)

    def get_technology_by_id(self, **kwargs):
        return self._call_inner_tool('get_technology_by_id', kwargs)

    def list_all_technologies(self, **kwargs):
        return self._call_inner_tool('list_all_technologies', kwargs)

    def list_domains_by_technology_name(self, **kwargs):
        return self._call_inner_tool('list_domains_by_technology_name', kwargs)

    def list_domains_by_technology_id(self, **kwargs):
        return self._call_inner_tool('list_domains_by_technology_id', kwargs)

    def list_technologies_by_domain_name(self, **kwargs):
        return self._call_inner_tool('list_technologies_by_domain_name', kwargs)

    def list_technologies_by_domain_id(self, **kwargs):
        return self._call_inner_tool('list_technologies_by_domain_id', kwargs)

    def get_domain_technology_mapping(self, **kwargs):
        return self._call_inner_tool('get_domain_technology_mapping', kwargs)

    def list_mappings_for_domain(self, **kwargs):
        return self._call_inner_tool('list_mappings_for_domain', kwargs)

    def list_mappings_for_technology(self, **kwargs):
        return self._call_inner_tool('list_mappings_for_technology', kwargs)

    def check_mapping_exists(self, **kwargs):
        return self._call_inner_tool('check_mapping_exists', kwargs)

    def get_mapping_metadata(self, **kwargs):
        return self._call_inner_tool('get_mapping_metadata', kwargs)

    def add_domain(self, **kwargs):
        return self._call_inner_tool('add_domain', kwargs)

    def remove_domain(self, **kwargs):
        return self._call_inner_tool('remove_domain', kwargs)

    def update_domain_info(self, **kwargs):
        return self._call_inner_tool('update_domain_info', kwargs)

    def add_technology(self, **kwargs):
        return self._call_inner_tool('add_technology', kwargs)

    def remove_technology(self, **kwargs):
        return self._call_inner_tool('remove_technology', kwargs)

    def update_technology_info(self, **kwargs):
        return self._call_inner_tool('update_technology_info', kwargs)

    def add_domain_technology_mapping(self, **kwargs):
        return self._call_inner_tool('add_domain_technology_mapping', kwargs)

    def remove_domain_technology_mapping(self, **kwargs):
        return self._call_inner_tool('remove_domain_technology_mapping', kwargs)

    def update_mapping_metadata(self, **kwargs):
        return self._call_inner_tool('update_mapping_metadata', kwargs)

