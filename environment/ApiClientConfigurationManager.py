# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, Optional, TypedDict, Any



class AuthenticationInfo(TypedDict):
    auth_type: str
    credentials: Any  # In real use, would be more strictly typed based on auth_type
    token_expiration: Optional[str]

class RetryPolicyInfo(TypedDict):
    max_retries: int
    backoff_strategy: str
    retryable_status_codes: List[int]

class ApiClientInfo(TypedDict):
    client_id: str
    name: str
    endpoint_url: str
    authentication: AuthenticationInfo
    timeout: float
    caching_enabled: bool
    retry_policy: RetryPolicyInfo
    logging_enabled: bool
    additional_features: Dict[str, Any]

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for managing multiple API client configurations, endpoints, and features.
        """

        # ApiClients: {client_id: ApiClientInfo}
        # Represents a single configured API connection with all essential and optional properties required for API interactions.
        self.api_clients: Dict[str, ApiClientInfo] = {}

        # Constraints:
        # - Each ApiClient must have a unique client_id or name.
        # - endpoint_url must be valid and unique for each ApiClient.
        # - Optional features (like caching, retries, logging) can be independently toggled per ApiClient.
        # - Disabling features should not affect unrelated configuration settings for the same ApiClient or other ApiClients.
        # - Authentication credentials must be kept secure and should conform to the required format for the given auth_type.

    def get_api_client_by_name(self, name: str) -> dict:
        """
        Retrieve ApiClientInfo for the specified client by its unique name.

        Args:
            name (str): The unique name of the API client.

        Returns:
            dict: 
              - If found: { "success": True, "data": ApiClientInfo }
              - If not found: { "success": False, "error": "API client with that name does not exist." }
        Constraints:
            - Client names are unique (at most one match expected).
        """
        for client_info in self.api_clients.values():
            if client_info["name"] == name:
                return { "success": True, "data": client_info }
        return { "success": False, "error": "API client with that name does not exist." }

    def get_api_client_by_id(self, client_id: str) -> dict:
        """
        Retrieve ApiClientInfo for the specified client by its unique client_id.

        Args:
            client_id (str): The unique identifier of the API client.

        Returns:
            dict: {
                "success": True,
                "data": ApiClientInfo
            }
            or
            {
                "success": False,
                "error": str  # Reason the client could not be found
            }

        Constraints:
            - client_id must exist in the api_clients dictionary.
        """
        if client_id not in self.api_clients:
            return {
                "success": False,
                "error": f"No ApiClient with client_id '{client_id}' found."
            }
        return {
            "success": True,
            "data": self.api_clients[client_id]
        }

    def list_all_api_clients(self) -> dict:
        """
        Return a list of all configured API clients.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[ApiClientInfo],  # List of all API client configurations (may be empty)
            }

        Constraints:
            - None for this operation (read-only).
        """
        result = list(self.api_clients.values())
        return {
            "success": True,
            "data": result
        }

    def check_client_feature_status(self, client_id: str, feature: str) -> dict:
        """
        Query the enabled status of a specified feature (e.g., 'caching', 'logging', 'retries') for a given ApiClient.

        Args:
            client_id (str): The client_id for the API client to query.
            feature (str): The feature to check ('caching', 'logging', or 'retries').

        Returns:
            dict: {
                "success": True,
                "enabled": bool | dict,  # bool for caching/logging, bool or dict info for retries
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - client_id must exist.
            - feature must be one of: 'caching', 'logging', 'retries'.
        """
        client = self.api_clients.get(client_id)
        if not client:
            return { "success": False, "error": "ApiClient with the specified client_id does not exist." }

        feature_lc = feature.lower()
        if feature_lc == "caching":
            return { "success": True, "enabled": client.get("caching_enabled", False) }
        elif feature_lc == "logging":
            return { "success": True, "enabled": client.get("logging_enabled", False) }
        elif feature_lc == "retries":
            retry_policy = client.get("retry_policy")
            enabled = False
            if retry_policy and isinstance(retry_policy, dict):
                enabled = retry_policy.get("max_retries", 0) > 0
            return { "success": True, "enabled": enabled }
        else:
            return { "success": False, "error": "Unknown or unsupported feature name. Supported: 'caching', 'logging', 'retries'." }

    def check_client_endpoint_uniqueness(self, endpoint_url: str) -> dict:
        """
        Checks if the provided endpoint_url is unique across all configured ApiClients.

        Args:
            endpoint_url (str): The endpoint URL to check for uniqueness.

        Returns:
            dict:
                {
                    "success": True,
                    "data": bool  # True if unique (not present), False otherwise
                }
        Constraints:
            - endpoint_url uniqueness is determined by comparing with all ApiClient's endpoint_url values.
            - Performs a string equality check.
        """
        for client in self.api_clients.values():
            if client["endpoint_url"] == endpoint_url:
                return { "success": True, "data": False }

        return { "success": True, "data": True }

    def get_authentication_info(self, client_id: str) -> dict:
        """
        Retrieve authentication information (auth_type, credentials, token_expiration) for a specific ApiClient.

        Args:
            client_id (str): The unique identifier of the ApiClient.

        Returns:
            dict:
                - {"success": True, "data": AuthenticationInfo}
                - {"success": False, "error": <reason>}
        Constraints:
            - client_id must match an existing ApiClient.
        """
        client = self.api_clients.get(client_id)
        if not client:
            return {"success": False, "error": "ApiClient not found"}

        authentication_info = client.get("authentication")
        if not authentication_info:
            return {"success": False, "error": "Authentication information missing for this ApiClient"}

        return {"success": True, "data": authentication_info}

    def get_retry_policy_info(self, client_id: str) -> dict:
        """
        Retrieve the retry policy settings for a specific ApiClient.

        Args:
            client_id (str): The unique identifier of the ApiClient.

        Returns:
            dict:
                - On success: {
                      "success": True,
                      "data": RetryPolicyInfo  # The retry policy configuration for the specified client
                  }
                - On failure: {
                      "success": False,
                      "error": "ApiClient not found"
                  }

        Constraints:
            - client_id must exist in the configuration manager.
        """
        client = self.api_clients.get(client_id)
        if not client:
            return {"success": False, "error": "ApiClient not found"}
        return {"success": True, "data": client["retry_policy"]}

    def set_caching_enabled(self, client_id: str, enabled: bool) -> dict:
        """
        Set the caching_enabled flag for a specific ApiClient.

        Args:
            client_id (str): Unique identifier for the ApiClient.
            enabled (bool): The value to set for caching_enabled.

        Returns:
            dict: {
                "success": True,
                "message": "Caching enabled flag set to <enabled> for ApiClient <client_id>."
            }
            or
            {
                "success": False,
                "error": "ApiClient with client_id <client_id> not found."
            }

        Constraints:
            - Only updates the caching_enabled property for the specified ApiClient.
            - Does not affect other features or clients.
            - ApiClient must exist.
        """
        client = self.api_clients.get(client_id)
        if client is None:
            return {
                "success": False,
                "error": f"ApiClient with client_id {client_id} not found."
            }

        client["caching_enabled"] = enabled
        return {
            "success": True,
            "message": f"Caching enabled flag set to {enabled} for ApiClient {client_id}."
        }

    def set_logging_enabled(self, client_id: str, enabled: bool) -> dict:
        """
        Set the logging_enabled flag for a specific ApiClient.
    
        Args:
            client_id (str): The unique identifier for the ApiClient.
            enabled (bool): The desired state of the logging_enabled flag.
    
        Returns:
            dict: {
                "success": True,
                "message": "Logging enabled set to <enabled> for ApiClient <client_id>"
            }
            or
            {
                "success": False,
                "error": "ApiClient with client_id <client_id> does not exist"
            }
    
        Constraints:
            - Modifies only the logging_enabled attribute for the specified ApiClient.
            - Does not affect unrelated configuration settings.
        """
        if client_id not in self.api_clients:
            return { "success": False, "error": f"ApiClient with client_id {client_id} does not exist" }
    
        self.api_clients[client_id]["logging_enabled"] = enabled
        return { "success": True, "message": f"Logging enabled set to {enabled} for ApiClient {client_id}" }

    def set_retry_policy(
        self,
        client_id: str,
        max_retries: int,
        backoff_strategy: str,
        retryable_status_codes: list
    ) -> dict:
        """
        Update the retry policy parameters for a specific ApiClient.

        Args:
            client_id (str): The unique client identifier.
            max_retries (int): Maximum number of retry attempts (must be >= 0).
            backoff_strategy (str): Retry backoff algorithm/strategy.
            retryable_status_codes (list): List of HTTP status codes (ints) to retry.

        Returns:
            dict: 
                On success:
                {
                    "success": True,
                    "message": "Retry policy updated for client_id <client_id>"
                }
                On failure:
                {
                    "success": False,
                    "error": "reason"
                }

        Constraints:
            - Only updates the retry_policy for the specified ApiClient.
            - Does not affect other features or clients.
            - max_retries must be >= 0.
            - backoff_strategy must be a non-empty string.
            - retryable_status_codes must be a list of valid HTTP status codes (ints, 100-599).
        """
        # Validate client existence
        if client_id not in self.api_clients:
            return { "success": False, "error": f"ApiClient with client_id {client_id} does not exist" }

        # Validate max_retries
        if not isinstance(max_retries, int) or max_retries < 0:
            return { "success": False, "error": "max_retries must be a non-negative integer" }

        # Validate backoff_strategy
        if not isinstance(backoff_strategy, str) or not backoff_strategy.strip():
            return { "success": False, "error": "backoff_strategy must be a non-empty string" }

        # Validate retryable_status_codes
        if (not isinstance(retryable_status_codes, list) or
            not all(isinstance(code, int) and 100 <= code <= 599 for code in retryable_status_codes)):
            return { "success": False, "error": "retryable_status_codes must be a list of HTTP status code integers (100-599)" }

        # Perform update (preserve other settings)
        self.api_clients[client_id]['retry_policy'] = {
            "max_retries": max_retries,
            "backoff_strategy": backoff_strategy,
            "retryable_status_codes": retryable_status_codes
        }

        return {
            "success": True,
            "message": f"Retry policy updated for client_id {client_id}"
        }

    def update_timeout(self, client_id: str, timeout: float) -> dict:
        """
        Change the timeout setting (in seconds) for a particular ApiClient.

        Args:
            client_id (str): The unique client ID identifying the ApiClient.
            timeout (float): The new timeout value in seconds (must be > 0).

        Returns:
            dict: 
                On success:
                    {"success": True, "message": "Timeout updated for client <client_id>"}
                On failure:
                    {"success": False, "error": "<reason>"}

        Constraints:
            - client_id must exist in api_clients.
            - timeout must be a positive number.
            - Only modifies the timeout for the specified ApiClient.
        """
        # Check existence
        if client_id not in self.api_clients:
            return {"success": False, "error": f"ApiClient with client_id '{client_id}' does not exist."}

        # Validate timeout
        if not isinstance(timeout, (float, int)):
            return {"success": False, "error": "Timeout must be a number."}
        if timeout <= 0:
            return {"success": False, "error": "Timeout must be greater than zero."}

        # Update
        self.api_clients[client_id]["timeout"] = float(timeout)
        return {"success": True, "message": f"Timeout updated for client {client_id}"}

    def update_authentication_info(
        self,
        client_id: str,
        auth_type: str,
        credentials: Any,
        token_expiration: Optional[str] = None
    ) -> dict:
        """
        Update the authentication information (auth_type, credentials, token_expiration)
        for the specified ApiClient.

        Args:
            client_id (str): The identifier for the ApiClient to update.
            auth_type (str): Authentication method/type (e.g., 'APIKey', 'OAuth').
            credentials (Any): Credentials required for the given auth_type.
            token_expiration (Optional[str]): Optional expiration time for the auth token.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Authentication info updated for ApiClient <client_id>"
                    }
                On failure:
                    {
                        "success": False,
                        "error": <reason>
                    }

        Constraints:
            - client_id must exist in api_clients.
            - auth_type must be non-empty.
            - credentials must be non-empty.
            - Does not update unrelated settings.
        """

        if client_id not in self.api_clients:
            return { "success": False, "error": f"ApiClient with client_id '{client_id}' does not exist" }

        if not auth_type or not isinstance(auth_type, str):
            return { "success": False, "error": "Invalid or missing auth_type" }

        if credentials is None or (isinstance(credentials, str) and credentials.strip() == ""):
            return { "success": False, "error": "Credentials must be provided and non-empty" }

        # (Further auth_type/credentials validation could be added if more details are specified)

        client_info = self.api_clients[client_id]
        client_info["authentication"]["auth_type"] = auth_type
        client_info["authentication"]["credentials"] = credentials
        client_info["authentication"]["token_expiration"] = token_expiration

        return {
            "success": True,
            "message": f"Authentication info updated for ApiClient '{client_id}'"
        }

    def update_endpoint_url(self, client_id: str, new_endpoint_url: str) -> dict:
        """
        Change the endpoint_url for a given ApiClient, ensuring uniqueness across all clients.

        Args:
            client_id (str): The unique identifier of the ApiClient to update.
            new_endpoint_url (str): The new endpoint URL to set.

        Returns:
            dict: {
                "success": True,
                "message": str  # Success message on update,
            }
            or
            {
                "success": False,
                "error": str  # Error message: client not found, endpoint not unique, etc.
            }

        Constraints:
            - Each ApiClient's endpoint_url must be unique.
            - Only update the target client; others are unaffected.
        """
        if client_id not in self.api_clients:
            return { "success": False, "error": f"ApiClient with client_id '{client_id}' does not exist." }

        # Check uniqueness: the new endpoint_url must not be assigned to any other client
        for cid, client in self.api_clients.items():
            if cid != client_id and client['endpoint_url'] == new_endpoint_url:
                return { "success": False, "error": "Another ApiClient already uses the specified endpoint_url." }

        self.api_clients[client_id]['endpoint_url'] = new_endpoint_url

        return {
            "success": True,
            "message": f"Endpoint URL updated for client '{client_id}'."
        }

    def add_api_client(
        self,
        client_id: str,
        name: str,
        endpoint_url: str,
        authentication: AuthenticationInfo,
        timeout: float,
        caching_enabled: bool,
        retry_policy: RetryPolicyInfo,
        logging_enabled: bool,
        additional_features: Dict[str, Any]
    ) -> dict:
        """
        Add/register a new ApiClient configuration, enforcing constraints (unique name/client_id and unique endpoint_url).

        Args:
            client_id (str): Unique identifier for the ApiClient.
            name (str): Unique name for the ApiClient.
            endpoint_url (str): Unique API endpoint.
            authentication (AuthenticationInfo): Authentication settings.
            timeout (float): Timeout in seconds.
            caching_enabled (bool): Whether caching is enabled.
            retry_policy (RetryPolicyInfo): Retry configuration.
            logging_enabled (bool): Whether logging is enabled.
            additional_features (dict): Extra per-client features.

        Returns:
            dict: {
                "success": True,
                "message": "ApiClient <client_id> added successfully."
            }
            or
            {
                "success": False,
                "error": str (Cause of failure)
            }

        Constraints:
            - client_id and name must be unique.
            - endpoint_url must be unique across all clients.
            - Do not overwrite existing clients.
        """
        # Check unique client_id
        if client_id in self.api_clients:
            return { "success": False, "error": f"client_id '{client_id}' already exists." }
    
        # Check unique name and endpoint_url
        for client in self.api_clients.values():
            if client["name"] == name:
                return { "success": False, "error": f"name '{name}' already exists." }
            if client["endpoint_url"] == endpoint_url:
                return { "success": False, "error": f"endpoint_url '{endpoint_url}' already exists." }

        # Build the client info
        api_client_info: ApiClientInfo = {
            "client_id": client_id,
            "name": name,
            "endpoint_url": endpoint_url,
            "authentication": authentication,
            "timeout": timeout,
            "caching_enabled": caching_enabled,
            "retry_policy": retry_policy,
            "logging_enabled": logging_enabled,
            "additional_features": additional_features
        }
        # Register the new client
        self.api_clients[client_id] = api_client_info

        return { "success": True, "message": f"ApiClient '{client_id}' added successfully." }

    def remove_api_client(self, client_id: Optional[str] = None, name: Optional[str] = None) -> dict:
        """
        Remove a specific ApiClient by client_id or name.

        Args:
            client_id (str, optional): The unique client_id of the ApiClient to remove.
            name (str, optional): The unique name of the ApiClient to remove.

        Returns:
            dict: {
                "success": True,
                "message": "ApiClient '<identifier>' removed successfully"
            }
            or
            {
                "success": False,
                "error": "Description of reason for failure"
            }

        Constraints:
            - Must provide at least one of client_id or name.
            - If both provided, they must refer to the same ApiClient.
            - The ApiClient must exist.
            - Removal only affects the specified ApiClient.
        """
        if not client_id and not name:
            return {
                "success": False,
                "error": "At least one of client_id or name must be provided."
            }

        # Fast path: try client_id lookup
        client_to_remove = None
        if client_id:
            client_info = self.api_clients.get(client_id)
            if client_info:
                if name and client_info["name"] != name:
                    return {
                        "success": False,
                        "error": (
                            "Provided client_id and name do not refer to the same ApiClient."
                        )
                    }
                # Found by client_id (and name matches if provided)
                client_to_remove = client_id
            elif name:
                # If not found by ID, try name only
                for cid, info in self.api_clients.items():
                    if info["name"] == name:
                        client_to_remove = cid
                        break
                if client_to_remove is None:
                    return {
                        "success": False,
                        "error": "ApiClient not found by client_id or name."
                    }
            else:
                return {
                    "success": False,
                    "error": "ApiClient with the specified client_id does not exist."
                }
        else:
            # Only name provided
            for cid, info in self.api_clients.items():
                if info["name"] == name:
                    client_to_remove = cid
                    break
            if client_to_remove is None:
                return {
                    "success": False,
                    "error": "ApiClient with the specified name does not exist."
                }

        # Remove the entry
        removed_client = self.api_clients.pop(client_to_remove)
        identifier = removed_client["name"] if removed_client.get("name") else removed_client["client_id"]

        return {
            "success": True,
            "message": f"ApiClient '{identifier}' removed successfully"
        }

    def set_additional_feature(self, client_id: str, feature_name: str, feature_value: Any) -> dict:
        """
        Enable, disable, or set a specified additional feature for a given ApiClient.

        Args:
            client_id (str): The unique ID of the ApiClient.
            feature_name (str): The name/key of the feature to set.
            feature_value (Any): The value to set for this feature.

        Returns:
            dict: {
                "success": True,
                "message": "Feature '<feature_name>' updated for ApiClient '<client_id>'"
            }
            or
            {
                "success": False,
                "error": "ApiClient with client_id '<client_id>' does not exist."
            }

        Constraints:
            - Only modifies the given client's additional_features, does not affect others.
            - client_id must exist.
        """
        client = self.api_clients.get(client_id)
        if client is None:
            return {
                "success": False,
                "error": f"ApiClient with client_id '{client_id}' does not exist."
            }

        # Set or update the feature in additional_features
        client["additional_features"][feature_name] = feature_value

        return {
            "success": True,
            "message": f"Feature '{feature_name}' updated for ApiClient '{client_id}'"
        }

    def update_api_client_name(self, client_id: str, new_name: str) -> dict:
        """
        Change the 'name' of an ApiClient, ensuring the new name is unique among all ApiClients.

        Args:
            client_id (str): The client_id of the ApiClient to update.
            new_name (str): The new name to assign to the ApiClient.

        Returns:
            dict: 
                On success:
                    {"success": True, "message": "ApiClient name updated successfully"}
                On error:
                    {"success": False, "error": "..."}
        Constraints:
            - client_id must exist.
            - new_name must be unique (not used by any other ApiClient).
        """
        # Check that the client exists
        if client_id not in self.api_clients:
            return { "success": False, "error": "ApiClient with specified client_id does not exist" }
    
        # Check if the new_name is already in use (by a different client_id)
        for cid, info in self.api_clients.items():
            if info["name"] == new_name and cid != client_id:
                return { "success": False, "error": "ApiClient name must be unique; the new name is already in use" }
    
        # (Optional: If new_name is same as current, just confirm success)
        if self.api_clients[client_id]["name"] == new_name:
            return { "success": True, "message": "ApiClient name is already set to the given name" }
    
        # Update the name
        self.api_clients[client_id]["name"] = new_name
        return { "success": True, "message": "ApiClient name updated successfully" }

    def update_api_client_id(self, old_client_id: str, new_client_id: str) -> dict:
        """
        Change the client_id of an existing ApiClient, ensuring uniqueness.

        Args:
            old_client_id (str): The client_id of the ApiClient to update.
            new_client_id (str): The new client_id to assign.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "message": "ApiClient client_id updated from <old> to <new>."
                    }
                - On failure:
                    {
                        "success": False,
                        "error": <reason>
                    }

        Constraints:
            - Each ApiClient must have a unique client_id.
            - The old_client_id must exist.
            - The new_client_id must not already exist.
        """
        if old_client_id not in self.api_clients:
            return {
                "success": False,
                "error": "Old client_id does not exist."
            }
        if new_client_id in self.api_clients:
            return {
                "success": False,
                "error": "New client_id already exists."
            }
        if old_client_id == new_client_id:
            return {
                "success": False,
                "error": "New client_id is the same as the old client_id."
            }

        # Update the client's id in the object and key
        client_info = self.api_clients.pop(old_client_id)
        client_info["client_id"] = new_client_id
        self.api_clients[new_client_id] = client_info

        return {
            "success": True,
            "message": f"ApiClient client_id updated from {old_client_id} to {new_client_id}."
        }


class ApiClientConfigurationManager(BaseEnv):
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

    def get_api_client_by_name(self, **kwargs):
        return self._call_inner_tool('get_api_client_by_name', kwargs)

    def get_api_client_by_id(self, **kwargs):
        return self._call_inner_tool('get_api_client_by_id', kwargs)

    def list_all_api_clients(self, **kwargs):
        return self._call_inner_tool('list_all_api_clients', kwargs)

    def check_client_feature_status(self, **kwargs):
        return self._call_inner_tool('check_client_feature_status', kwargs)

    def check_client_endpoint_uniqueness(self, **kwargs):
        return self._call_inner_tool('check_client_endpoint_uniqueness', kwargs)

    def get_authentication_info(self, **kwargs):
        return self._call_inner_tool('get_authentication_info', kwargs)

    def get_retry_policy_info(self, **kwargs):
        return self._call_inner_tool('get_retry_policy_info', kwargs)

    def set_caching_enabled(self, **kwargs):
        return self._call_inner_tool('set_caching_enabled', kwargs)

    def set_logging_enabled(self, **kwargs):
        return self._call_inner_tool('set_logging_enabled', kwargs)

    def set_retry_policy(self, **kwargs):
        return self._call_inner_tool('set_retry_policy', kwargs)

    def update_timeout(self, **kwargs):
        return self._call_inner_tool('update_timeout', kwargs)

    def update_authentication_info(self, **kwargs):
        return self._call_inner_tool('update_authentication_info', kwargs)

    def update_endpoint_url(self, **kwargs):
        return self._call_inner_tool('update_endpoint_url', kwargs)

    def add_api_client(self, **kwargs):
        return self._call_inner_tool('add_api_client', kwargs)

    def remove_api_client(self, **kwargs):
        return self._call_inner_tool('remove_api_client', kwargs)

    def set_additional_feature(self, **kwargs):
        return self._call_inner_tool('set_additional_feature', kwargs)

    def update_api_client_name(self, **kwargs):
        return self._call_inner_tool('update_api_client_name', kwargs)

    def update_api_client_id(self, **kwargs):
        return self._call_inner_tool('update_api_client_id', kwargs)

