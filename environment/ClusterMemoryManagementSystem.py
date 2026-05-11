# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
from typing import Optional



class NodeInfo(TypedDict):
    node_id: str
    node_name: str
    role: str
    memory_allocated: float
    memory_max: float
    memory_min: float
    sta: str  # Status

class ClusterInfo(TypedDict):
    cluster_id: str
    cluster_name: str
    node_list: List[str]  # List of node_ids
    policy: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for managing memory and resources in a compute cluster.
        """

        # Nodes: {node_id: NodeInfo}
        # Holds all resource-allocation and status information for each node
        self.nodes: Dict[str, NodeInfo] = {}

        # Clusters: {cluster_id: ClusterInfo}
        # Contains node membership and policy enforcement at the cluster level
        self.clusters: Dict[str, ClusterInfo] = {}

        # Constraints:
        # - memory_allocated for a node must be between memory_min and memory_max for that node.
        # - Node names and/or IDs must be unique within the cluster.
        # - No memory update is allowed if it would exceed the node’s physical memory capacity.
        # - Cluster-level policies may limit total allocated memory or enforce minimum allocations across all nodes.

    @staticmethod
    def _get_physical_capacity(node_info: NodeInfo) -> float:
        if node_info.get("physical_memory_capacity") is not None:
            return float(node_info["physical_memory_capacity"])
        if node_info.get("physical_capacity") is not None:
            return float(node_info["physical_capacity"])
        return float(node_info["memory_max"])

    @staticmethod
    def _has_modeled_physical_capacity(node_info: NodeInfo) -> bool:
        return (
            node_info.get("physical_memory_capacity") is not None
            or node_info.get("physical_capacity") is not None
        )

    def get_node_by_name(self, node_name: str) -> dict:
        """
        Retrieve a node's complete resource and identification info given its node_name.

        Args:
            node_name (str): The name of the node to search for.

        Returns:
            dict: 
              { "success": True, "data": NodeInfo } if found,
              { "success": False, "error": "Node not found" } otherwise.

        Constraints:
            - Node names are unique within the cluster.
        """
        if not node_name or not isinstance(node_name, str):
            return { "success": False, "error": "Node not found" }
    
        for node_info in self.nodes.values():
            if node_info["node_name"] == node_name:
                return { "success": True, "data": node_info }
    
        return { "success": False, "error": "Node not found" }

    def get_node_by_id(self, node_id: str) -> dict:
        """
        Retrieve a node's complete information by its node_id.

        Args:
            node_id (str): The identifier of the node.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": NodeInfo    # Complete information of the node.
                    }
                On failure (node_id not found):
                    {
                        "success": False,
                        "error": "Node with given node_id does not exist"
                    }

        Constraints:
            - node_id must exist in the nodes dictionary.
        """
        node_info = self.nodes.get(node_id)
        if node_info is None:
            return { "success": False, "error": "Node with given node_id does not exist" }
        return { "success": True, "data": node_info }

    def list_all_nodes(self) -> dict:
        """
        Retrieve a list of all nodes with their key information.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[NodeInfo]  # List of nodes' information (may be empty)
            }

        Notes:
            - No input parameters.
            - Always succeeds, even if there are no nodes (returns an empty list).
        """
        nodes_list = list(self.nodes.values())
        return { "success": True, "data": nodes_list }

    def get_cluster_by_node(self, node_id: str) -> dict:
        """
        Retrieve the cluster info for the cluster containing the specified node.

        Args:
            node_id (str): The unique identifier of the node.

        Returns:
            dict: {
                "success": True,
                "data": ClusterInfo  # The info of the cluster this node belongs to
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g. node does not exist or not assigned to any cluster
            }

        Constraints:
            - The node must exist.
            - The node must be assigned to some cluster.
        """
        if node_id not in self.nodes:
            return {"success": False, "error": "Node does not exist"}

        for cluster_info in self.clusters.values():
            if node_id in cluster_info["node_list"]:
                return {"success": True, "data": cluster_info}

        return {"success": False, "error": "Node is not assigned to any cluster"}

    def get_node_memory_limits(self, node_id: str) -> dict:
        """
        Get memory_min, memory_max, and memory_allocated for a specified node.

        Args:
            node_id (str): The unique identifier for the target node.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "memory_min": float,
                    "memory_max": float,
                    "memory_allocated": float
                }
            }
            or
            {
                "success": False,
                "error": str
            }
    
        Constraints:
            - node_id must exist in the system.
        """
        node = self.nodes.get(node_id)
        if node is None:
            return {"success": False, "error": "Node not found"}
    
        limits = {
            "memory_min": node["memory_min"],
            "memory_max": node["memory_max"],
            "memory_allocated": node["memory_allocated"]
        }
        return {"success": True, "data": limits}

    def get_node_physical_capacity(self, node_id: str) -> dict:
        """
        Query the physical memory capacity of the given node (its maximum possible memory).

        Args:
            node_id (str): Unique identifier for the node.

        Returns:
            dict:
                If successful:
                    {
                        'success': True,
                        'data': {
                            'node_id': str,
                            'physical_memory_capacity': float
                        }
                    }
                If node not found:
                    {
                        'success': False,
                        'error': 'Node not found'
                    }
        """
        node = self.nodes.get(node_id)
        if node is None:
            return {"success": False, "error": "Node not found"}
        physical_capacity = self._get_physical_capacity(node)
        return {
            "success": True,
            "data": {
                "node_id": node_id,
                "physical_memory_capacity": physical_capacity
            }
        }

    def get_cluster_policy(self, cluster_id: str) -> dict:
        """
        Retrieve the memory management policy and settings for a specified cluster.

        Args:
            cluster_id (str): The ID of the cluster for which to retrieve the policy.

        Returns:
            dict:
                - On success: { "success": True, "data": <policy: str> }
                - On failure: { "success": False, "error": "Cluster does not exist" }

        Constraints:
            - The given cluster_id must exist in the system.
        """
        cluster = self.clusters.get(cluster_id)
        if cluster is None:
            return { "success": False, "error": "Cluster does not exist" }

        return { "success": True, "data": cluster["policy"] }

    def list_cluster_nodes(self, cluster_id: str) -> dict:
        """
        List all nodes (ids and names) that belong to the specified cluster.

        Args:
            cluster_id (str): Unique identifier of the cluster.

        Returns:
            dict:
                - success: True and data: list of { "node_id": ..., "node_name": ... } on success.
                - success: False and error: "Cluster does not exist" if cluster_id is invalid.

        Constraints:
            - Cluster must exist.
            - Returned list may be empty if no nodes are in the cluster.
        """
        if cluster_id not in self.clusters:
            return { "success": False, "error": "Cluster does not exist" }

        cluster_info = self.clusters[cluster_id]
        node_id_list = cluster_info.get("node_list", [])
        result = []
        for node_id in node_id_list:
            node_info = self.nodes.get(node_id)
            if node_info is not None:
                result.append({
                    "node_id": node_id,
                    "node_name": node_info["node_name"]
                })
            # If node_id in node_list but not in nodes, can ignore or skip

        return { "success": True, "data": result }

    def get_total_cluster_memory_allocated(self, cluster_id: str) -> dict:
        """
        Sum current memory_allocated of all nodes in a given cluster.

        Args:
            cluster_id (str): The unique identifier of the cluster.

        Returns:
            dict: {
                "success": True,
                "data": float  # The total allocated memory (sum over referenced nodes)
            }
            or
            {
                "success": False,
                "error": str
            }

        Notes:
            - If a cluster includes node IDs that are not present in self.nodes, these are ignored.
            - If the cluster does not exist, returns an error.
        """
        cluster = self.clusters.get(cluster_id)
        if not cluster:
            return { "success": False, "error": "Cluster does not exist" }

        total_memory = 0.0
        for node_id in cluster["node_list"]:
            node_info = self.nodes.get(node_id)
            if node_info is not None:
                total_memory += node_info.get("memory_allocated", 0.0)

        return { "success": True, "data": total_memory }

    def check_node_name_uniqueness(self, cluster_id: str, node_name: str) -> dict:
        """
        Verify whether a given node_name is unique within the specified cluster.

        Args:
            cluster_id (str): The ID of the cluster in which to check for uniqueness.
            node_name  (str): The node name to check.

        Returns:
            dict: {
                "success": True,
                "data": bool  # True if unique, False if already present
            }
            or
            {
                "success": False,
                "error": str  # Error message (e.g., cluster does not exist)
            }

        Constraints:
            - The cluster must exist.
            - Compares name only among nodes in the given cluster's node_list.
        """
        if cluster_id not in self.clusters:
            return { "success": False, "error": "Cluster does not exist" }

        cluster = self.clusters[cluster_id]
        for node_id in cluster["node_list"]:
            node = self.nodes.get(node_id)
            if node is not None:
                if node["node_name"] == node_name:
                    return { "success": True, "data": False }  # Not unique

        return { "success": True, "data": True }  # Unique

    def update_node_memory_allocated(self, node_id: str, new_memory_allocated: float) -> dict:
        """
        Set the memory_allocated value for a node after validating against node and cluster constraints.

        Args:
            node_id (str): The ID of the node to update.
            new_memory_allocated (float): The new memory_allocated value to assign.

        Returns:
            dict: 
                - On success:
                    {
                        "success": True,
                        "message": "Node memory_allocated updated to ..."
                    }
                - On failure:
                    {
                        "success": False,
                        "error": "reason"
                    }

        Constraints:
            - node_id must exist in the system.
            - new_memory_allocated must be numeric, >=0, >= memory_min and <= memory_max for the node.
            - Must not exceed node's physical memory capacity (assumed capped by memory_max).
            - May not violate cluster total memory allocation policies, if applicable.
        """
        # Check if node exists
        node_info = self.nodes.get(node_id)
        if not node_info:
            return {"success": False, "error": f"Node with id '{node_id}' does not exist"}

        # Validity checks for new_memory_allocated
        try:
            mem = float(new_memory_allocated)
            if mem < 0:
                return {"success": False, "error": "new_memory_allocated must be non-negative"}
        except (ValueError, TypeError):
            return {"success": False, "error": "new_memory_allocated must be a valid floating point number"}

        # Constraint: Should be within node's memory_min and memory_max
        if mem < node_info["memory_min"]:
            return {"success": False, "error": f"memory_allocated must be >= memory_min ({node_info['memory_min']})"}
        if mem > node_info["memory_max"]:
            return {"success": False, "error": f"memory_allocated must be <= memory_max ({node_info['memory_max']})"}
        physical_capacity = self._get_physical_capacity(node_info)
        if self._has_modeled_physical_capacity(node_info) and mem > physical_capacity:
            return {"success": False, "error": f"memory_allocated must be <= physical memory capacity ({physical_capacity})"}

        # Check for cluster-level policy (if node is in a cluster and policy is applicable)
        # Find the cluster this node belongs to
        cluster_found = None
        for cluster in self.clusters.values():
            if node_id in cluster["node_list"]:
                cluster_found = cluster
                break

        if cluster_found:
            policy = cluster_found.get("policy")
            if policy:
                # For simplicity, if the policy is a string like "max_total=X", enforce it
                if policy.startswith("max_total="):
                    try:
                        max_total = float(policy.split("=", 1)[1])
                    except ValueError:
                        return {"success": False, "error": f"Invalid cluster policy value: {policy}"}
                    # Calculate what the new total would be
                    total_allocated = 0.0
                    for nid in cluster_found["node_list"]:
                        # For the target node, use the NEW value; others use current
                        if nid == node_id:
                            total_allocated += mem
                        else:
                            total_allocated += self.nodes[nid]["memory_allocated"]
                    if total_allocated > max_total:
                        return {"success": False, "error":
                                f"Policy violation: total allocated memory ({total_allocated}) would exceed cluster max ({max_total})"}

        # All checks passed, perform update
        node_info["memory_allocated"] = mem

        return {
            "success": True,
            "message": f"Node '{node_id}' memory_allocated updated to {mem}"
        }

    def update_node_memory_limits(
        self,
        node_id: str,
        memory_min: float = None,
        memory_max: float = None
    ) -> dict:
        """
        Set or change the memory_min and/or memory_max of a node.
        Applies all constraint validations:
            - Node must exist.
            - memory_min and memory_max (if provided) must be non-negative.
            - If both provided: memory_min <= memory_max.
            - After update, memory_allocated must be in [memory_min, memory_max].
            - No value may exceed node's physical capacity (if such capacity is modeled).

        Args:
            node_id (str): ID of the node to update.
            memory_min (float, optional): New minimum allocation.
            memory_max (float, optional): New maximum allocation.

        Returns:
            dict: {
                "success": True,
                "message": "Updated memory limits for node X: min=..., max=...",
            } or {
                "success": False,
                "error": error_message
            }
        """
        # 1. Check node exists
        node = self.nodes.get(node_id)
        if node is None:
            return { "success": False, "error": "Node not found" }

        old_min = node["memory_min"]
        old_max = node["memory_max"]
        memory_allocated = node["memory_allocated"]

        # 2. Validate new min/max if provided
        new_min = memory_min if memory_min is not None else old_min
        new_max = memory_max if memory_max is not None else old_max

        if new_min < 0 or new_max < 0:
            return { "success": False, "error": "Memory limits must be non-negative" }
        if new_min > new_max:
            return { "success": False, "error": "memory_min cannot be greater than memory_max" }
        new_min = float(new_min)
        new_max = float(new_max)

        # 3. Ensure allocated in new [min, max]
        if not (new_min <= memory_allocated <= new_max):
            return { "success": False, "error": "Current memory_allocated does not fit in new min/max range" }

        # 4. Check against physical memory capacity if such capacity is modeled
        # Let's assume, if node has 'physical_capacity' attribute,
        # neither min nor max can exceed it
        physical_capacity = self._get_physical_capacity(node)
        if self._has_modeled_physical_capacity(node) and (new_min > physical_capacity or new_max > physical_capacity):
            return { "success": False, "error": "Limits cannot exceed node's physical memory capacity" }

        # 5. Commit changes
        node["memory_min"] = new_min
        node["memory_max"] = new_max
        self.nodes[node_id] = node

        return {
            "success": True,
            "message": (
                f"Updated memory limits for node {node_id}: "
                f"min={new_min}, max={new_max}"
            )
        }

    def change_node_status(self, node_id: str, new_status: str) -> dict:
        """
        Update the status ('sta') of a node.

        Args:
            node_id (str): The identifier of the node to update.
            new_status (str): The new status to assign (e.g., 'active', 'maintenance', 'offline').

        Returns:
            dict: {
                "success": True,
                "message": "Node <node_id> status updated to <new_status>."
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (e.g., node not found)
            }

        Constraints:
            - The node_id must exist in the cluster.
            - No restriction on acceptable status values unless specified elsewhere.
        """
        if node_id not in self.nodes:
            return {"success": False, "error": f"Node '{node_id}' does not exist"}

        self.nodes[node_id]["sta"] = new_status
        return {
            "success": True,
            "message": f"Node '{node_id}' status updated to '{new_status}'."
        }


    def add_node_to_cluster(self, cluster_id: str, node_id: Optional[str]=None, node_info: Optional[NodeInfo]=None) -> dict:
        """
        Add an existing or new node to a specified cluster.

        Args:
            cluster_id (str): The cluster to which to add the node.
            node_id (Optional[str]): The ID of an existing node to add. Provide ONLY for existing nodes.
            node_info (Optional[NodeInfo]): Info for a new node to create and add. Provide ONLY for new nodes.

        Returns:
            dict:
                On success: { "success": True, "message": "Node <node_id> added to cluster <cluster_id>" }
                On error:   { "success": False, "error": "error description" }

        Constraints:
            - Exactly one of node_id or node_info must be provided.
            - Node IDs and names must be unique within the cluster.
            - Node cannot already be in the cluster.
            - If creating a new node, its ID and name must *not* exist cluster-wide.
            - Cluster must exist.
        """
        # Check that cluster exists
        cluster = self.clusters.get(cluster_id)
        if not cluster:
            return { "success": False, "error": f"Cluster {cluster_id} does not exist." }

        if (node_id is None and node_info is None) or (node_id and node_info):
            return { "success": False, "error": "Specify exactly one of node_id (existing node) or node_info (new node)." }

        # Adding an existing node
        if node_id is not None:
            # Check node exists
            node = self.nodes.get(node_id)
            if node is None:
                return { "success": False, "error": f"Node {node_id} does not exist." }

            # Already in cluster?
            if node_id in cluster['node_list']:
                return { "success": False, "error": f"Node {node_id} is already in cluster {cluster_id}." }

            # Uniqueness of node name and id within the target cluster
            for n_id in cluster['node_list']:
                n = self.nodes.get(n_id)
                if n and (n['node_id'] == node['node_id'] or n['node_name'] == node['node_name']):
                    return { "success": False, "error": f"Node ID or name '{node['node_id']}/{node['node_name']}' already exists in cluster." }

            # Add node to cluster
            cluster['node_list'].append(node_id)
            return { "success": True, "message": f"Node {node_id} added to cluster {cluster_id}" }

        # Adding a new node
        else:
            # Validate node_info keys
            node_id_new = node_info.get('node_id')
            node_name_new = node_info.get('node_name')
            if not node_id_new or not node_name_new:
                return { "success": False, "error": "NodeInfo must include node_id and node_name." }

            # Uniqueness of node_id and node_name cluster-wide
            for node in self.nodes.values():
                if node['node_id'] == node_id_new:
                    return { "success": False, "error": f"Node ID {node_id_new} already exists in system." }
                if node['node_name'] == node_name_new:
                    return { "success": False, "error": f"Node name {node_name_new} already exists in system." }

            # Uniqueness in the cluster
            for n_id in cluster['node_list']:
                n = self.nodes.get(n_id)
                if n and (n['node_id'] == node_id_new or n['node_name'] == node_name_new):
                    return { "success": False, "error": f"Node ID or name '{node_id_new}/{node_name_new}' already exists in cluster." }

            # Add the new node to system
            self.nodes[node_id_new] = node_info.copy()

            # Add node to cluster
            cluster['node_list'].append(node_id_new)
            return { "success": True, "message": f"Node {node_id_new} added to cluster {cluster_id}" }

    def remove_node_from_cluster(self, cluster_id: str, node_id: str) -> dict:
        """
        Remove a node from the node list of a given cluster.

        Args:
            cluster_id (str): The ID of the cluster from which the node will be removed.
            node_id (str): The ID of the node to remove.

        Returns:
            dict:
                On success: { "success": True, "message": "Node <node_id> removed from cluster <cluster_id>." }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - Cluster and node must exist.
            - Node must be a member of the cluster's node_list.
            - Other node properties or cluster policies are not modified by this operation.
        """
        if cluster_id not in self.clusters:
            return { "success": False, "error": f"Cluster {cluster_id} does not exist." }
        if node_id not in self.nodes:
            return { "success": False, "error": f"Node {node_id} does not exist." }
    
        cluster = self.clusters[cluster_id]
        if node_id not in cluster["node_list"]:
            return { "success": False, "error": f"Node {node_id} is not a member of cluster {cluster_id}." }

        # Remove node_id from cluster's node_list
        cluster["node_list"].remove(node_id)

        return { "success": True, "message": f"Node {node_id} removed from cluster {cluster_id}." }

    def update_cluster_policy(self, cluster_id: str, policy: str) -> dict:
        """
        Change the resource/memory policy for the specified cluster.

        Args:
            cluster_id (str): The ID of the cluster to update.
            policy (str): The new memory/resource allocation policy for the cluster.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Policy updated for cluster <cluster_id>" }
                On error:
                    { "success": False, "error": str }
        Constraints:
            - The given cluster_id must exist.
            - The new policy string must not be empty.
        """
        if not cluster_id or cluster_id not in self.clusters:
            return { "success": False, "error": "Cluster does not exist" }
    
        if not isinstance(policy, str) or policy.strip() == "":
            return { "success": False, "error": "Policy string must be non-empty" }

        self.clusters[cluster_id]["policy"] = policy
        return { "success": True, "message": f"Policy updated for cluster {cluster_id}" }


class ClusterMemoryManagementSystem(BaseEnv):
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

    def get_node_by_name(self, **kwargs):
        return self._call_inner_tool('get_node_by_name', kwargs)

    def get_node_by_id(self, **kwargs):
        return self._call_inner_tool('get_node_by_id', kwargs)

    def list_all_nodes(self, **kwargs):
        return self._call_inner_tool('list_all_nodes', kwargs)

    def get_cluster_by_node(self, **kwargs):
        return self._call_inner_tool('get_cluster_by_node', kwargs)

    def get_node_memory_limits(self, **kwargs):
        return self._call_inner_tool('get_node_memory_limits', kwargs)

    def get_node_physical_capacity(self, **kwargs):
        return self._call_inner_tool('get_node_physical_capacity', kwargs)

    def get_cluster_policy(self, **kwargs):
        return self._call_inner_tool('get_cluster_policy', kwargs)

    def list_cluster_nodes(self, **kwargs):
        return self._call_inner_tool('list_cluster_nodes', kwargs)

    def get_total_cluster_memory_allocated(self, **kwargs):
        return self._call_inner_tool('get_total_cluster_memory_allocated', kwargs)

    def check_node_name_uniqueness(self, **kwargs):
        return self._call_inner_tool('check_node_name_uniqueness', kwargs)

    def update_node_memory_allocated(self, **kwargs):
        return self._call_inner_tool('update_node_memory_allocated', kwargs)

    def update_node_memory_limits(self, **kwargs):
        return self._call_inner_tool('update_node_memory_limits', kwargs)

    def change_node_status(self, **kwargs):
        return self._call_inner_tool('change_node_status', kwargs)

    def add_node_to_cluster(self, **kwargs):
        return self._call_inner_tool('add_node_to_cluster', kwargs)

    def remove_node_from_cluster(self, **kwargs):
        return self._call_inner_tool('remove_node_from_cluster', kwargs)

    def update_cluster_policy(self, **kwargs):
        return self._call_inner_tool('update_cluster_policy', kwargs)
