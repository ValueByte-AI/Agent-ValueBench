# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, Optional, TypedDict



class ProxyInfo(TypedDict):
    proxy_id: str
    ip_address: str
    port: int
    protocol: str
    username: Optional[str]
    password: Optional[str]
    status: str
    last_used_time: float
    fail_count: int
    health_score: float  # corrected typo 'health_sco'

class ProxyPoolInfo(TypedDict):
    pool_id: str
    proxies: List[str]  # list of proxy_ids
    rotation_policy: str
    current_index: int

class _GeneratedEnvImpl:
    def __init__(self):
        """
        The environment for managing a rotating proxy pool.
        """

        # Proxies: {proxy_id: ProxyInfo}
        # Represents an individual proxy server.
        self.proxies: Dict[str, ProxyInfo] = {}

        # Proxy pools: {pool_id: ProxyPoolInfo}
        # Represents a collection of proxies and how rotation is managed.
        self.proxy_pools: Dict[str, ProxyPoolInfo] = {}

        # Constraints:
        # - Only proxies with status="active" can be selected for rotation.
        # - Removing a proxy deletes it from the proxy pool’s proxy list.
        # - The system must handle empty pool cases gracefully.
        # - The current_index must be updated appropriately upon addition or removal of proxies.
        # - If using authentication, username and password are required for applicable protocols.

    @staticmethod
    def _protocol_requires_auth(protocol: str) -> bool:
        return str(protocol or "").lower() in {"socks4", "socks5", "ftp"}

    def get_pool_by_id(self, pool_id: str) -> dict:
        """
        Retrieve details of a proxy pool, including its list of proxy_ids, rotation policy,
        and the current index for rotation.

        Args:
            pool_id (str): Identifier of the proxy pool.

        Returns:
            dict: {
                "success": True,
                "data": ProxyPoolInfo  # details of the pool (proxies list, policy, index, etc.)
            }
            or
            {
                "success": False,
                "error": str  # e.g., "Proxy pool does not exist"
            }

        Constraints:
            - The specified pool_id must exist in the environment's proxy_pools.
        """
        pool = self.proxy_pools.get(pool_id)
        if pool is None:
            return { "success": False, "error": "Proxy pool does not exist" }
        return { "success": True, "data": pool }

    def list_proxy_ids_in_pool(self, pool_id: str) -> dict:
        """
        List all proxy_ids currently included in a specified proxy pool.

        Args:
            pool_id (str): The unique identifier for the proxy pool.

        Returns:
            dict: {
                "success": True,
                "data": List[str],  # The list of proxy_ids in the pool (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Error message if the pool does not exist.
            }

        Constraints:
            - The pool_id must exist in the system.
            - Returns an empty list if pool exists but contains no proxy_ids.
        """
        pool = self.proxy_pools.get(pool_id)
        if pool is None:
            return {"success": False, "error": "Proxy pool does not exist"}
        return {"success": True, "data": list(pool["proxies"])}

    def get_proxy_info(self, proxy_id: str) -> dict:
        """
        Retrieve full metadata for a specific proxy using its proxy_id.

        Args:
            proxy_id (str): The identifier of the proxy to query.

        Returns:
            dict: 
                {"success": True, "data": ProxyInfo} if found,
                {"success": False, "error": "Proxy not found"} otherwise.

        Constraints:
            - proxy_id must exist in the system.
        """
        proxy_info = self.proxies.get(proxy_id)
        if proxy_info is None:
            return {"success": False, "error": "Proxy not found"}
        return {"success": True, "data": proxy_info}

    def get_active_proxies_in_pool(self, pool_id: str) -> dict:
        """
        Lists proxy_ids for proxies in the specified pool that are currently status="active".

        Args:
            pool_id (str): The proxy pool's unique identifier.

        Returns:
            dict: {
                "success": True,
                "data": List[str],  # List of proxy_ids with status="active"
            }
            or
            {
                "success": False,
                "error": str  # Error message if pool does not exist
            }

        Constraints:
            - Only proxies with status == "active" are included.
            - If the pool does not exist, return an error.
            - If the pool has no proxies (empty list) or no active proxies, return empty list with success.
        """
        # Check if the pool exists
        pool = self.proxy_pools.get(pool_id)
        if pool is None:
            return {"success": False, "error": "Proxy pool does not exist"}

        # Get list of proxy_ids in the pool
        proxy_ids = pool.get("proxies", [])

        # Filter proxies by status "active"
        active_proxy_ids = [
            proxy_id
            for proxy_id in proxy_ids
            if proxy_id in self.proxies and self.proxies[proxy_id]["status"] == "active"
        ]

        return {"success": True, "data": active_proxy_ids}

    def check_proxy_status(self, proxy_id: str) -> dict:
        """
        Query the current status (active, inactive, etc.) of a specific proxy.

        Args:
            proxy_id (str): The unique identifier of the proxy.

        Returns:
            dict: {
                "success": True,
                "data": { "proxy_id": str, "status": str }
            }
            or
            {
                "success": False,
                "error": str  # Reason the query failed (e.g., Proxy not found)
            }

        Constraints:
            - proxy_id must exist in the proxies dictionary.
        """
        proxy = self.proxies.get(proxy_id)
        if not proxy:
            return { "success": False, "error": "Proxy not found" }
        return {
            "success": True,
            "data": { "proxy_id": proxy_id, "status": proxy["status"] }
        }

    def get_protocol_auth_requirements(self, proxy_ids: list) -> dict:
        """
        Determine if the protocols used by the given proxies require authentication (username/password).

        Args:
            proxy_ids (list of str): List of proxy IDs to check.

        Returns:
            dict: {
                "success": True,
                "data": Dict[str, bool],  # Mapping from proxy_id to bool (True if protocol requires authentication)
            }
            or
            {
                "success": False,
                "error": str  # Description of the error
            }

        Constraints:
            - For unknown proxy_id, indicate error in mapping.
            - Uses internal knowledge of protocol authentication requirements.
        """
        # Define protocol requirements (example - can be expanded)
        if not isinstance(proxy_ids, list):
            return {"success": False, "error": "proxy_ids must be a list of strings (proxy IDs)"}

        result = {}
        for proxy_id in proxy_ids:
            proxy = self.proxies.get(proxy_id)
            if not proxy:
                result[proxy_id] = "proxy_not_found"
            else:
                result[proxy_id] = self._protocol_requires_auth(proxy.get("protocol", ""))

        return {
            "success": True,
            "data": result
        }

    def get_current_index_in_pool(self, pool_id: str) -> dict:
        """
        Inspect the current rotation index for a given proxy pool.

        Args:
            pool_id (str): The unique identifier of the target proxy pool.

        Returns:
            dict: {
                "success": True,
                "data": int  # The current rotation index for the pool.
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., pool not found or malformed data.
            }

        Constraints:
            - The specified pool_id must exist in the system.
        """
        pool_info = self.proxy_pools.get(pool_id)
        if not pool_info:
            return { "success": False, "error": "Proxy pool does not exist" }
        if "current_index" not in pool_info:
            return { "success": False, "error": "current_index not defined for pool" }

        return {
            "success": True,
            "data": pool_info["current_index"]
        }

    def pool_is_empty(self, pool_id: str) -> dict:
        """
        Check whether the specified proxy pool currently contains any proxies.

        Args:
            pool_id (str): The identifier of the proxy pool.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": bool  # True if the pool contains zero proxies, else False
                    }
                On error (e.g., pool_id does not exist):
                    {
                        "success": False,
                        "error": str  # reason
                    }

        Constraints:
            - The specified pool_id must exist in the proxy_pools.
        """
        pool_info = self.proxy_pools.get(pool_id)
        if pool_info is None:
            return {"success": False, "error": "Proxy pool not found"}
        is_empty = len(pool_info.get('proxies', [])) == 0
        return {"success": True, "data": is_empty}

    def get_proxy_usage_statistics(self, proxy_id: str) -> dict:
        """
        Retrieve usage statistics for a given proxy.

        Args:
            proxy_id (str): The unique identifier for the proxy.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "fail_count": int,
                    "last_used_time": float,
                    "health_score": float
                }
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., proxy not found)
            }

        Constraints:
            - proxy_id must exist in the proxy registry.
        """
        proxy = self.proxies.get(proxy_id)
        if not proxy:
            return {"success": False, "error": "Proxy not found"}

        stats = {
            "fail_count": proxy["fail_count"],
            "last_used_time": proxy["last_used_time"],
            "health_score": proxy["health_score"]
        }
        return {"success": True, "data": stats}

    def add_proxy_to_pool(self, pool_id: str, proxy_id: str) -> dict:
        """
        Add a proxy (by proxy_id) into a specified proxy pool.
        Updates the proxy list and adjusts the rotation index if needed.

        Args:
            pool_id (str): The proxy pool to add the proxy to.
            proxy_id (str): The ID of the proxy to add.

        Returns:
            dict: 
                On success: {"success": True, "message": "..."}
                On failure: {"success": False, "error": "..."}
    
        Constraints:
            - pool_id must exist in the proxy_pools.
            - proxy_id must exist in the proxies dict.
            - proxy_id must not already be in pool's proxy list.
            - If the pool was empty, set current_index to 0.
            - If proxies exist already, keep current_index unchanged.
        """
        if pool_id not in self.proxy_pools:
            return {"success": False, "error": "Proxy pool does not exist."}
        if proxy_id not in self.proxies:
            return {"success": False, "error": "Proxy does not exist."}

        pool = self.proxy_pools[pool_id]
        if proxy_id in pool["proxies"]:
            return {"success": False, "error": "Proxy already in the pool."}

        # Add the proxy_id to the pool's proxies list
        pool["proxies"].append(proxy_id)

        # Adjust current_index if necessary
        if len(pool["proxies"]) == 1:
            # Pool was empty before, now has one proxy
            pool["current_index"] = 0
        else:
            # Ensure current_index remains valid (should already be so)
            if pool["current_index"] < 0 or pool["current_index"] >= len(pool["proxies"]):
                pool["current_index"] = 0  # fallback safety

        self.proxy_pools[pool_id] = pool

        return {
            "success": True,
            "message": f"Proxy '{proxy_id}' added to proxy pool '{pool_id}'."
        }

    def remove_proxy_from_pool(self, pool_id: str, proxy_id: str) -> dict:
        """
        Remove a given proxy from a specified proxy pool, ensuring proxy list and current_index are updated appropriately.

        Args:
            pool_id (str): Identifier of the proxy pool.
            proxy_id (str): Identifier of the proxy to be removed.

        Returns:
            dict: {
                "success": True,
                "message": "Proxy <proxy_id> removed from pool <pool_id>."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - If the pool does not exist, return an error.
            - If the proxy is not in the pool, return an error.
            - Removing the proxy updates the pool's proxies list and current_index.
            - Handles empty proxy list cases & current_index bounds.
        """
        pool = self.proxy_pools.get(pool_id)
        if pool is None:
            return {"success": False, "error": f"Proxy pool '{pool_id}' does not exist."}

        proxies = pool["proxies"]
        if proxy_id not in proxies:
            return {"success": False, "error": f"Proxy '{proxy_id}' is not in pool '{pool_id}'."}
    
        remove_index = proxies.index(proxy_id)
        proxies.pop(remove_index)

        # Adjust current_index
        if not proxies:
            pool["current_index"] = 0
        else:
            # If current_index pointed to the removed proxy or is now out of range
            if pool["current_index"] == remove_index or pool["current_index"] >= len(proxies):
                pool["current_index"] = 0
            elif pool["current_index"] > remove_index:
                pool["current_index"] -= 1  # shift left
    
        # Save back
        pool["proxies"] = proxies

        return {"success": True, "message": f"Proxy '{proxy_id}' removed from pool '{pool_id}'."}

    def delete_proxy(self, proxy_id: str) -> dict:
        """
        Completely delete a proxy from the system, including all pools it is a member of.

        Args:
            proxy_id (str): The unique identifier of the proxy to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Proxy <proxy_id> deleted from system and all pools"
            }
            or
            {
                "success": False,
                "error": "Proxy not found"
            }

        Constraints:
            - Removing a proxy deletes it from the proxy pool's list as well.
            - The system must handle empty pool cases gracefully.
            - The current_index of the pool should be updated: if out-of-bounds or proxies empty, set to 0.
        """
        if proxy_id not in self.proxies:
            return { "success": False, "error": "Proxy not found" }

        # Remove proxy from all pools
        for pool_info in self.proxy_pools.values():
            if proxy_id in pool_info["proxies"]:
                pool_info["proxies"] = [pid for pid in pool_info["proxies"] if pid != proxy_id]
                # After removal, update current_index
                proxies_len = len(pool_info["proxies"])
                if proxies_len == 0:
                    pool_info["current_index"] = 0
                elif pool_info["current_index"] >= proxies_len:
                    pool_info["current_index"] = 0  # wrap to start

        # Remove proxy from the global registry
        del self.proxies[proxy_id]

        return {
            "success": True,
            "message": f"Proxy {proxy_id} deleted from system and all pools"
        }

    def update_proxy_status(self, proxy_id: str, new_status: str) -> dict:
        """
        Change the status of a given proxy.

        Args:
            proxy_id (str): The unique identifier for the proxy whose status should be updated.
            new_status (str): The new status to assign (e.g., 'active', 'inactive', 'failed').

        Returns:
            dict: {
                "success": True,
                "message": "Status of proxy <proxy_id> changed to <new_status>"
            }
            or
            {
                "success": False,
                "error": "Proxy not found"
            }

        Constraints:
            - The proxy_id must exist in the system.
            - No restriction on new_status value beyond being a string.
        """
        proxy = self.proxies.get(proxy_id)
        if not proxy:
            return { "success": False, "error": "Proxy not found" }
    
        proxy["status"] = new_status
        return {
            "success": True,
            "message": f"Status of proxy {proxy_id} changed to {new_status}"
        }

    def set_rotation_index(self, pool_id: str, new_index: int) -> dict:
        """
        Set the current_index field in a proxy pool.

        Args:
            pool_id (str): Identifier of the proxy pool to update.
            new_index (int): The index to set as current for proxy rotation.

        Returns:
            dict: On success: { "success": True, "message": "Set current_index of pool {pool_id} to {new_index}" }
                  On error: { "success": False, "error": str }

        Constraints:
            - The specified proxy pool must exist.
            - If the pool has proxies, new_index must be 0 <= new_index < len(proxies).
            - If the pool's proxy list is empty, only new_index == 0 is valid.
        """
        pool = self.proxy_pools.get(pool_id)
        if pool is None:
            return {"success": False, "error": f"Proxy pool '{pool_id}' does not exist"}

        num_proxies = len(pool["proxies"])
        if num_proxies == 0:
            if new_index != 0:
                return {"success": False, "error": "Proxy pool is empty; current_index can only be set to 0"}
        else:
            if not (0 <= new_index < num_proxies):
                return {
                    "success": False,
                    "error": f"new_index {new_index} out of range for pool proxies of length {num_proxies}"
                }

        pool["current_index"] = new_index

        return {
            "success": True,
            "message": f"Set current_index of pool '{pool_id}' to {new_index}"
        }

    def increment_rotation_index(self, pool_id: str) -> dict:
        """
        Advance the current rotation index to the next eligible 'active' proxy (wrap-around if needed).

        Args:
            pool_id (str): The ID of the proxy pool for rotation.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Rotation index updated to <new_index>.",
                    }
                On error:
                    {
                        "success": False,
                        "error": "<reason>"
                    }

        Constraints:
            - Only proxies with status='active' can be selected for rotation.
            - Handles empty pool and no-active-proxies gracefully, setting current_index to -1.
            - Wraps around if at end of rotation list.
        """
        pool = self.proxy_pools.get(pool_id)
        if not pool:
            return { "success": False, "error": "Pool does not exist." }

        proxy_ids = pool.get("proxies", [])
        if not proxy_ids:
            pool["current_index"] = -1
            return { "success": True, "message": "No proxies in pool. Rotation index set to -1." }

        # List of (index, proxy_id) where status is 'active'
        active_indices = [
            i for i, pid in enumerate(proxy_ids)
            if self.proxies.get(pid, {}).get("status") == "active"
        ]

        if not active_indices:
            pool["current_index"] = -1
            return { "success": True, "message": "No active proxies in pool. Rotation index set to -1." }

        current_index = pool.get("current_index", -1)

        # Find current position among active_indices (if current_index is already at an active proxy)
        try:
            current_active_pos = active_indices.index(current_index) if current_index in active_indices else -1
        except Exception:
            current_active_pos = -1

        # Compute next active index (wrap-around)
        if current_active_pos == -1:
            # start from first active proxy
            new_index = active_indices[0]
        else:
            next_pos = (current_active_pos + 1) % len(active_indices)
            new_index = active_indices[next_pos]

        pool["current_index"] = new_index

        return {
            "success": True,
            "message": f"Rotation index updated to {new_index}."
        }

    def add_new_proxy(
        self,
        proxy_id: str,
        ip_address: str,
        port: int,
        protocol: str,
        status: str,
        last_used_time: float,
        fail_count: int,
        health_score: float,
        username: Optional[str] = None,
        password: Optional[str] = None,
        pool_id: Optional[str] = None
    ) -> dict:
        """
        Insert a new proxy with the provided details into the system. Optionally, add the proxy to a specified pool.

        Args:
            proxy_id (str): Unique identifier for the proxy.
            ip_address (str): Proxy server IP address.
            port (int): Proxy server port.
            protocol (str): Proxy protocol (e.g., http, https, socks5).
            status (str): Proxy's operational status (should be e.g., "active", "inactive", etc.).
            last_used_time (float): Timestamp of last usage.
            fail_count (int): Number of recent consecutive failures.
            health_score (float): Proxy health score.
            username (Optional[str]): Authentication username if required.
            password (Optional[str]): Authentication password if required.
            pool_id (Optional[str]): If provided, add this proxy to the specified pool.

        Returns:
            dict: {
                "success": True,
                "message": "Proxy added",
                "proxy_id": str,
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - proxy_id must be unique.
            - If protocol requires authentication, username and password must be provided.
            - If pool_id is provided, it must exist.
            - If added to a pool, pool's proxies list and current_index are updated as needed.
        """
        # Required field check
        if not proxy_id or not ip_address or not protocol or port is None or status is None or last_used_time is None or fail_count is None or health_score is None:
            return { "success": False, "error": "Missing required proxy details." }

        # Unique proxy_id check
        if proxy_id in self.proxies:
            return { "success": False, "error": "proxy_id already exists." }

        # Protocol authentication requirement check
        # For demonstration, let's assume 'http', 'https' require auth if either username/password are set or protocol is in a predefined list
        if self._protocol_requires_auth(protocol):
            if not username or not password:
                return { "success": False, "error": "Username and password required for protocol '{}'.".format(protocol) }

        # Create the proxy entry
        proxy_info: ProxyInfo = {
            "proxy_id": proxy_id,
            "ip_address": ip_address,
            "port": port,
            "protocol": protocol,
            "username": username,
            "password": password,
            "status": status,
            "last_used_time": last_used_time,
            "fail_count": fail_count,
            "health_score": health_score
        }
        self.proxies[proxy_id] = proxy_info

        # Optionally add to pool
        if pool_id is not None:
            if pool_id not in self.proxy_pools:
                # Rollback proxy addition
                del self.proxies[proxy_id]
                return { "success": False, "error": f"Proxy pool '{pool_id}' does not exist." }
        
            pool = self.proxy_pools[pool_id]
            if proxy_id in pool["proxies"]:
                # Rollback
                del self.proxies[proxy_id]
                return { "success": False, "error": f"Proxy '{proxy_id}' already in pool '{pool_id}'." }
            pool["proxies"].append(proxy_id)
            # If this is the only proxy, reset current_index to 0
            if len(pool["proxies"]) == 1:
                pool["current_index"] = 0

        return { "success": True, "message": "Proxy added", "proxy_id": proxy_id }

    def handle_empty_pool(self, pool_id: str) -> dict:
        """
        Take appropriate action if a proxy pool becomes empty:
        - Sets the pool's current_index to -1 to indicate no available proxies.
        - Does nothing if the pool is not empty.
    
        Args:
            pool_id (str): The identifier of the proxy pool to check and handle.
        
        Returns:
            dict: {
                "success": True,
                "message": Description of action taken for the pool.
            }
            or
            {
                "success": False,
                "error": Error reason (e.g., proxy pool does not exist)
            }
    
        Constraints:
            - Pool must exist.
            - If the pool's `proxies` list is empty, set `current_index` to -1.
            - The system must handle empty pool cases gracefully.
        """
        pool = self.proxy_pools.get(pool_id)
        if pool is None:
            return { "success": False, "error": "Proxy pool does not exist" }

        if len(pool["proxies"]) == 0:
            pool["current_index"] = -1  # Mark as empty, unable to rotate
            return {
                "success": True,
                "message": f"Handled empty pool case for pool_id={pool_id}: set current_index to -1."
            }
        else:
            return {
                "success": True,
                "message": f"Pool {pool_id} is not empty. No action needed."
            }

    def update_proxy_auth_fields(
        self, proxy_id: str, username: Optional[str], password: Optional[str]
    ) -> dict:
        """
        Set username/password for a proxy as required by protocol.

        Args:
            proxy_id (str): The ID of the proxy to update.
            username (Optional[str]): The username for authentication. Must be provided if protocol requires auth.
            password (Optional[str]): The password for authentication. Must be provided if protocol requires auth.

        Returns:
            dict: {
                "success": True,
                "message": "Proxy authentication fields updated for proxy_id '<proxy_id>'"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - If protocol of proxy requires authentication, both username and password must be provided (not None or empty).
            - If protocol does not require authentication, authentication info will be cleared.
        """
        # Verify proxy exists
        proxy = self.proxies.get(proxy_id)
        if not proxy:
            return { "success": False, "error": f"Proxy with proxy_id '{proxy_id}' does not exist" }
    
        protocol = proxy["protocol"].lower()
        # Protocols that require authentication
        if self._protocol_requires_auth(protocol):
            # Protocol requires authentication
            if not username or not password:
                return {
                    "success": False,
                    "error": f"Protocol '{protocol}' requires username and password to be set"
                }
            proxy["username"] = username
            proxy["password"] = password
        else:
            # Protocol does not require authentication, clear any auth info
            proxy["username"] = None
            proxy["password"] = None

        self.proxies[proxy_id] = proxy  # Not strictly necessary in Python dicts, but explicit.

        return {
            "success": True,
            "message": f"Proxy authentication fields updated for proxy_id '{proxy_id}'"
        }


class RotatingProxyPoolManagementSystem(BaseEnv):
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

    def get_pool_by_id(self, **kwargs):
        return self._call_inner_tool('get_pool_by_id', kwargs)

    def list_proxy_ids_in_pool(self, **kwargs):
        return self._call_inner_tool('list_proxy_ids_in_pool', kwargs)

    def get_proxy_info(self, **kwargs):
        return self._call_inner_tool('get_proxy_info', kwargs)

    def get_active_proxies_in_pool(self, **kwargs):
        return self._call_inner_tool('get_active_proxies_in_pool', kwargs)

    def check_proxy_status(self, **kwargs):
        return self._call_inner_tool('check_proxy_status', kwargs)

    def get_protocol_auth_requirements(self, **kwargs):
        return self._call_inner_tool('get_protocol_auth_requirements', kwargs)

    def get_current_index_in_pool(self, **kwargs):
        return self._call_inner_tool('get_current_index_in_pool', kwargs)

    def pool_is_empty(self, **kwargs):
        return self._call_inner_tool('pool_is_empty', kwargs)

    def get_proxy_usage_statistics(self, **kwargs):
        return self._call_inner_tool('get_proxy_usage_statistics', kwargs)

    def add_proxy_to_pool(self, **kwargs):
        return self._call_inner_tool('add_proxy_to_pool', kwargs)

    def remove_proxy_from_pool(self, **kwargs):
        return self._call_inner_tool('remove_proxy_from_pool', kwargs)

    def delete_proxy(self, **kwargs):
        return self._call_inner_tool('delete_proxy', kwargs)

    def update_proxy_status(self, **kwargs):
        return self._call_inner_tool('update_proxy_status', kwargs)

    def set_rotation_index(self, **kwargs):
        return self._call_inner_tool('set_rotation_index', kwargs)

    def increment_rotation_index(self, **kwargs):
        return self._call_inner_tool('increment_rotation_index', kwargs)

    def add_new_proxy(self, **kwargs):
        return self._call_inner_tool('add_new_proxy', kwargs)

    def handle_empty_pool(self, **kwargs):
        return self._call_inner_tool('handle_empty_pool', kwargs)

    def update_proxy_auth_fields(self, **kwargs):
        return self._call_inner_tool('update_proxy_auth_fields', kwargs)
