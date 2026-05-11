# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



class ResourceInfo(TypedDict):
    resource_id: str
    title: str
    description: str
    author: str
    creation_date: str
    domain: str           # Must match a valid domain name
    tags: List[str]
    url: str

class DomainInfo(TypedDict):
    domain_id: str
    name: str
    description: str

class UserQueryInfo(TypedDict):
    query_id: str
    user_id: str
    domain_filter: str      # Should reference a valid domain name
    keyword_filter: str
    sort_order: str
    page_number: int        # Non-negative integer
    items_per_page: int     # Non-negative integer

class _GeneratedEnvImpl:
    def __init__(self):
        # Resources: {resource_id: ResourceInfo}
        # Resource attributes: resource_id, title, description, author, creation_date, domain, tags, url
        self.resources: Dict[str, ResourceInfo] = {}

        # Domains: {domain_id: DomainInfo}
        # Domain attributes: domain_id, name, description
        self.domains: Dict[str, DomainInfo] = {}

        # User queries: {query_id: UserQueryInfo}
        # UserQuery attributes: query_id, user_id, domain_filter, keyword_filter, sort_order, page_number, items_per_page
        self.user_queries: Dict[str, UserQueryInfo] = {}

        # Constraint notes:
        # - Resources must belong to exactly one domain.
        # - Pagination parameters (page_number, items_per_page) must be non-negative integers.
        # - Only valid domain names can be used as filters for queries.
        # - A page cannot contain more resources than the specified items_per_page value.

    def get_domains(self) -> dict:
        """
        Retrieve the list of all valid domains available in the portal.

        Returns:
            dict: {
                "success": True,
                "data": List[{"domain_id": str, "name": str}]
                # May be empty if no domains are present
            }
        """
        data = [
            {"domain_id": domain_info["domain_id"], "name": domain_info["name"]}
            for domain_info in self.domains.values()
        ]
        return { "success": True, "data": data }

    def get_domain_by_name(self, name: str) -> dict:
        """
        Retrieve details for a domain matching the specified name.
    
        Args:
            name (str): The domain name to look up.
        
        Returns:
            dict: {
                "success": True,
                "data": DomainInfo
            } 
            OR
            {
                "success": False,
                "error": "Domain not found"
            }
        
        Constraints:
            - Only valid (i.e., existing) domain names can be queried.
            - Domain name search is exact and case-sensitive.
        """
        if not isinstance(name, str) or not name.strip():
            return { "success": False, "error": "Domain not found" }
        for domain in self.domains.values():
            if domain["name"] == name:
                return { "success": True, "data": domain }
        return { "success": False, "error": "Domain not found" }

    def list_resources_by_domain(self, domain_name: str) -> dict:
        """
        List all resources assigned to a specific valid domain.

        Args:
            domain_name (str): The name of the domain to retrieve resources for.

        Returns:
            dict: {
                "success": True,
                "data": List[ResourceInfo]  # Might be empty if no resources assigned to domain
            }
            OR
            {
                "success": False,
                "error": str  # reason why operation failed (e.g. invalid domain)
            }

        Constraints:
            - Only valid domain names can be used as filters for queries.
            - Resources must belong to exactly one domain.
        """

        # Check if the domain name exists in any DomainInfo
        if not any(d['name'] == domain_name for d in self.domains.values()):
            return {
                "success": False,
                "error": f"Domain name '{domain_name}' does not exist."
            }

        # List all resources assigned to this domain
        resources = [
            resource for resource in self.resources.values()
            if resource['domain'] == domain_name
        ]

        return {
            "success": True,
            "data": resources
        }

    def paginate_resources(
        self, 
        resources: List[ResourceInfo], 
        page_number: int, 
        items_per_page: int
    ) -> dict:
        """
        Return the sublist of resources corresponding to the requested page, respecting pagination constraints.

        Args:
            resources (List[ResourceInfo]): Full resource list to paginate.
            page_number (int): The page number (0-based, must be >= 0).
            items_per_page (int): Number of items per page (must be >= 1).

        Returns:
            dict: {
                "success": True,
                "data": List[ResourceInfo]  # List of resources for the requested page (possibly empty)
            }
            or
            {
                "success": False,
                "error": str  # Explanation of error
            }

        Constraints:
            - page_number and items_per_page must be non-negative integers.
            - items_per_page must be >= 1.
            - Result list length will be ≤ items_per_page. 
        """
        # Check type and bounds for pagination parameters
        if not isinstance(page_number, int) or not isinstance(items_per_page, int):
            return {"success": False, "error": "Pagination parameters must be integers"}

        if page_number < 0:
            return {"success": False, "error": "page_number must be non-negative"}
        if items_per_page <= 0:
            return {"success": False, "error": "items_per_page must be a positive integer"}

        total_resources = len(resources)
        start_idx = page_number * items_per_page
        end_idx = start_idx + items_per_page

        if start_idx >= total_resources:
            # Page number is out of range; return empty data
            return {"success": True, "data": []}

        paginated = resources[start_idx:end_idx]
        return {"success": True, "data": paginated}

    def get_resource_by_id(self, resource_id: str) -> dict:
        """
        Retrieve metadata and details of a specific resource by its resource_id.

        Args:
            resource_id (str): Unique identifier for the resource.

        Returns:
            dict: 
                If found: { "success": True, "data": ResourceInfo }
                If not:   { "success": False, "error": "Resource not found" }
        Constraints:
            - resource_id must uniquely identify a resource in the portal.
        """
        resource = self.resources.get(resource_id)
        if not resource:
            return { "success": False, "error": "Resource not found" }
        return { "success": True, "data": resource }

    def search_resources_by_keyword(self, keyword: str, domain_filter: str = None) -> dict:
        """
        Retrieve resources matching a keyword in title, description, or tags, possibly filtered by domain.

        Args:
            keyword (str): Keyword to search for (case-insensitive substring match).
            domain_filter (str, optional): Domain name to restrict search to.
    
        Returns:
            dict: {
                "success": True,
                "data": List[ResourceInfo],  # Resources matching keyword (+ domain, if specified)
            }
            or
            {
                "success": False,
                "error": str  # Description of error (e.g., invalid domain)
            }

        Constraints:
            - Only valid domain names may be used as filter.
        """

        if not keyword or not isinstance(keyword, str):
            return {"success": False, "error": "Keyword must be a non-empty string"}

        keyword_lower = keyword.strip().lower()

        # Validate domain filter if provided
        if domain_filter:
            valid_domains = {d["name"] for d in self.domains.values()}
            if domain_filter not in valid_domains:
                return {"success": False, "error": "Invalid domain filter"}

        result = []
        for resource in self.resources.values():
            # Filter by domain if specified
            if domain_filter and resource["domain"] != domain_filter:
                continue

            # Check keyword in title or description
            title = resource["title"].lower()
            description = resource["description"].lower()
            tag_match = any(keyword_lower in tag.lower() for tag in resource["tags"])
            if (
                keyword_lower in title
                or keyword_lower in description
                or tag_match
            ):
                result.append(resource)

        return {"success": True, "data": result}

    def list_all_resources(self) -> dict:
        """
        List all available resources in the portal.

        Returns:
            dict: {
                "success": True,
                "data": List[ResourceInfo],  # List of all resources (possibly empty)
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - No explicit inputs or filters.
            - Returns the current list of all resources in the system.
        """
        try:
            all_resources = list(self.resources.values())
            return { "success": True, "data": all_resources }
        except Exception as e:
            return { "success": False, "error": f"Internal error: {e}" }

    def get_user_query_by_id(self, query_id: str) -> dict:
        """
        Retrieve metadata for a specific user query based on its unique query ID.

        Args:
            query_id (str): The unique identifier for the user query.

        Returns:
            dict:
                On success: {
                    "success": True,
                    "data": UserQueryInfo  # The stored info for this query_id
                }
                On failure: {
                    "success": False,
                    "error": "User query not found"
                }

        Constraints:
            - The queried ID must exist in stored user queries.
        """
        user_query = self.user_queries.get(query_id)
        if user_query is None:
            return {"success": False, "error": "User query not found"}
        return {"success": True, "data": user_query}

    def add_resource(
        self,
        resource_id: str,
        title: str,
        description: str,
        author: str,
        creation_date: str,
        domain: str,
        tags: list,
        url: str
    ) -> dict:
        """
        Add a new resource to the portal, assigning it to an existing domain.

        Args:
            resource_id (str): Unique identifier for the resource.
            title (str): Resource title.
            description (str): Resource description.
            author (str): Author name.
            creation_date (str): Creation date (string format).
            domain (str): Name of existing domain to assign resource to.
            tags (List[str]): List of tags.
            url (str): Resource URL.

        Returns:
            dict: {
                "success": True,
                "message": "Resource added: <resource_id>"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Resources must belong to exactly one (existing) domain, referenced by name.
            - Resource ID must be unique.
        """
        # Enforce uniqueness of resource ID
        if resource_id in self.resources:
            return {"success": False, "error": f"Resource ID '{resource_id}' already exists."}
    
        # Check domain validity (must match DomainInfo['name'])
        domain_names = {domain_info["name"] for domain_info in self.domains.values()}
        if domain not in domain_names:
            return {"success": False, "error": f"Domain '{domain}' does not exist."}

        resource_info = {
            "resource_id": resource_id,
            "title": title,
            "description": description,
            "author": author,
            "creation_date": creation_date,
            "domain": domain,
            "tags": tags,
            "url": url
        }
        self.resources[resource_id] = resource_info

        return {"success": True, "message": f"Resource added: {resource_id}"}

    def update_resource(self, resource_id: str, updates: dict) -> dict:
        """
        Modify the details or metadata of an existing resource.

        Args:
            resource_id (str): The unique ID of the resource to update.
            updates (dict): Dictionary containing keys and new values for ResourceInfo fields
                            (except 'resource_id', which cannot be changed).

        Returns:
            dict: {
                "success": True,
                "message": "Resource updated successfully"
            }
            or
            dict: {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The resource must exist.
            - If the 'domain' is being updated, it must reference a valid domain name (that exists in self.domains.values()).
            - resource_id cannot be changed.
            - All other updates override the existing values for that resource.
        """
        # Check resource existence
        if resource_id not in self.resources:
            return {"success": False, "error": "Resource does not exist"}

        # Prevent changing resource_id
        if "resource_id" in updates and updates["resource_id"] != resource_id:
            return {"success": False, "error": "Resource ID cannot be changed"}

        # Validate domain if to be updated
        if "domain" in updates:
            new_domain = updates["domain"]
            valid_domains = set(domain_info["name"] for domain_info in self.domains.values())
            if new_domain not in valid_domains:
                return {"success": False, "error": f"Domain '{new_domain}' does not exist"}

        # Validate pagination, tags if any (not strictly required; handle at insert/update time)
        # Can add more checks if needed

        # Allowed keys to be updated (cannot update resource_id)
        modifiable_keys = {"title", "description", "author", "creation_date", "domain", "tags", "url"}

        # Filter updates to only allowed fields
        filtered_updates = {k: v for k, v in updates.items() if k in modifiable_keys}

        if not filtered_updates:
            return {"success": False, "error": "No updatable fields provided"}

        # Update resource
        self.resources[resource_id].update(filtered_updates)
        return {"success": True, "message": "Resource updated successfully"}

    def delete_resource(self, resource_id: str) -> dict:
        """
        Remove an existing resource from the portal by its unique resource_id.

        Args:
            resource_id (str): The ID of the resource to remove.

        Returns:
            dict: {
                "success": True,
                "message": str,  # Success message
            }
            or
            {
                "success": False,
                "error": str     # Reason for failure (e.g., not found)
            }

        Constraints:
            - The resource with the specified resource_id must exist in the portal.
        """
        if resource_id not in self.resources:
            return { "success": False, "error": "Resource not found." }
        del self.resources[resource_id]
        return { "success": True, "message": f"Resource {resource_id} deleted successfully." }

    def add_domain(self, domain_id: str, name: str, description: str) -> dict:
        """
        Add a new subject domain/category to organize resources.

        Args:
            domain_id (str): Unique identifier for the domain (must not duplicate an existing domain's id).
            name (str): Unique name for the domain (must not duplicate existing domain name).
            description (str): Description for the domain.

        Returns:
            dict: {
                "success": True,
                "message": "Domain added successfully."
            }
            or
            {
                "success": False,
                "error": <reason str>
            }

        Constraints:
            - domain_id and name must be unique (not present in self.domains or any domain's name).
            - All fields are required and cannot be empty.
        """
        if not domain_id or not name or not description:
            return {"success": False, "error": "All fields (domain_id, name, description) must be provided and non-empty."}

        if domain_id in self.domains:
            return {"success": False, "error": "Domain ID already exists."}

        # Check for duplicate name
        for domain in self.domains.values():
            if domain["name"] == name:
                return {"success": False, "error": "Domain name already exists."}

        # Add domain
        self.domains[domain_id] = {
            "domain_id": domain_id,
            "name": name,
            "description": description,
        }
        return {"success": True, "message": "Domain added successfully."}

    def update_domain(self, domain_id: str, name: str = None, description: str = None) -> dict:
        """
        Modify the name and/or description of an existing domain.

        Args:
            domain_id (str): Identifier of the domain to modify.
            name (str, optional): New name for the domain. Must be unique if specified.
            description (str, optional): New description.

        Returns:
            dict: {
                "success": True,
                "message": "Domain updated."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Domain must exist.
            - If a new name is provided, it must not duplicate another domain's name.
            - Name/description, if provided, must be non-empty strings.
        """
        if domain_id not in self.domains:
            return {"success": False, "error": "Domain not found."}

        domain = self.domains[domain_id]
    
        # Validate new name if provided
        if name is not None:
            if not isinstance(name, str) or not name.strip():
                return {"success": False, "error": "Domain name must be a non-empty string."}
            # Must not duplicate another domain's name (excluding self)
            for did, d in self.domains.items():
                if did != domain_id and d["name"] == name:
                    return {"success": False, "error": "Domain name already exists."}
    
        if description is not None:
            if not isinstance(description, str) or not description.strip():
                return {"success": False, "error": "Domain description must be a non-empty string."}
    
        # Update fields if provided
        old_name = domain["name"]
        if name is not None:
            domain["name"] = name
        if description is not None:
            domain["description"] = description

        self.domains[domain_id] = domain

        if name is not None and name != old_name:
            for resource in self.resources.values():
                if resource["domain"] == old_name:
                    resource["domain"] = name

        return {"success": True, "message": "Domain updated."}

    def record_user_query(
        self,
        query_id: str,
        user_id: str,
        domain_filter: str,
        keyword_filter: str,
        sort_order: str,
        page_number: int,
        items_per_page: int
    ) -> dict:
        """
        Store a user's query (including domain filter, keyword, sort preference, pagination) for reference or analytics.
        Constraints:
            - page_number and items_per_page must be non-negative integers.
            - If domain_filter is not empty, it must match an existing domain name.
            - query_id must be unique (not already recorded).

        Args:
            query_id (str): Unique ID for this query record.
            user_id (str): Identifier of the user making the query.
            domain_filter (str): Domain filter (should match a valid domain name or be empty).
            keyword_filter (str): Keyword filter string.
            sort_order (str): Sort order requested.
            page_number (int): Page index (must be >= 0).
            items_per_page (int): Items per page (must be >= 0).

        Returns:
            dict: {
                "success": True,
                "message": "User query recorded successfully."
            } or {
                "success": False,
                "error": "<error description>"
            }
        """
        # Unique query_id check
        if query_id in self.user_queries:
            return { "success": False, "error": "Query ID already exists." }
    
        # Pagination parameter check
        if not (isinstance(page_number, int) and page_number >= 0):
            return { "success": False, "error": "page_number must be a non-negative integer." }
        if not (isinstance(items_per_page, int) and items_per_page >= 0):
            return { "success": False, "error": "items_per_page must be a non-negative integer." }
    
        # Valid domain name check (if filter is not blank)
        if domain_filter:
            valid_domain_names = {domain["name"] for domain in self.domains.values()}
            if domain_filter not in valid_domain_names:
                return { "success": False, "error": "Invalid domain_filter: specified domain does not exist." }
    
        self.user_queries[query_id] = {
            "query_id": query_id,
            "user_id": user_id,
            "domain_filter": domain_filter,
            "keyword_filter": keyword_filter,
            "sort_order": sort_order,
            "page_number": page_number,
            "items_per_page": items_per_page
        }
        return { "success": True, "message": "User query recorded successfully." }

    def delete_domain(self, domain_id: str) -> dict:
        """
        Remove an existing domain and delete all resources assigned to it.

        Args:
            domain_id (str): The ID of the domain to delete.

        Returns:
            dict:
                Success: {
                    "success": True,
                    "message": "Domain '<name>' deleted and <N> resource(s) removed."
                }
                Failure: {
                    "success": False,
                    "error": "Domain with id <domain_id> does not exist."
                }

        Constraints:
            - Domain must exist.
            - All resources must belong to one valid domain; when domain is deleted, associated resources are removed.
        """
        # Check domain existence
        if domain_id not in self.domains:
            return {
                "success": False,
                "error": f"Domain with id {domain_id} does not exist."
            }
        domain_name = self.domains[domain_id]['name']

        # Find and delete all resources assigned to this domain
        to_delete = [res_id for res_id, res in self.resources.items() if res['domain'] == domain_name]
        for res_id in to_delete:
            del self.resources[res_id]

        # Delete the domain itself
        del self.domains[domain_id]

        return {
            "success": True,
            "message": f"Domain '{domain_name}' deleted and {len(to_delete)} resource(s) removed."
        }


class KnowledgeManagementPortal(BaseEnv):
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

    def get_domains(self, **kwargs):
        return self._call_inner_tool('get_domains', kwargs)

    def get_domain_by_name(self, **kwargs):
        return self._call_inner_tool('get_domain_by_name', kwargs)

    def list_resources_by_domain(self, **kwargs):
        return self._call_inner_tool('list_resources_by_domain', kwargs)

    def paginate_resources(self, **kwargs):
        return self._call_inner_tool('paginate_resources', kwargs)

    def get_resource_by_id(self, **kwargs):
        return self._call_inner_tool('get_resource_by_id', kwargs)

    def search_resources_by_keyword(self, **kwargs):
        return self._call_inner_tool('search_resources_by_keyword', kwargs)

    def list_all_resources(self, **kwargs):
        return self._call_inner_tool('list_all_resources', kwargs)

    def get_user_query_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_query_by_id', kwargs)

    def add_resource(self, **kwargs):
        return self._call_inner_tool('add_resource', kwargs)

    def update_resource(self, **kwargs):
        return self._call_inner_tool('update_resource', kwargs)

    def delete_resource(self, **kwargs):
        return self._call_inner_tool('delete_resource', kwargs)

    def add_domain(self, **kwargs):
        return self._call_inner_tool('add_domain', kwargs)

    def update_domain(self, **kwargs):
        return self._call_inner_tool('update_domain', kwargs)

    def record_user_query(self, **kwargs):
        return self._call_inner_tool('record_user_query', kwargs)

    def delete_domain(self, **kwargs):
        return self._call_inner_tool('delete_domain', kwargs)
