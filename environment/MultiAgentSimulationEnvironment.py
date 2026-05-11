# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, Any, TypedDict



class AgentInfo(TypedDict):
    agent_id: str
    position: str  # Use str for generality; could be made more specific if needed.
    environment_id: str
    current_action: str
    knowledge_base: Dict[str, Any]  # knowledge_base may have arbitrary keys/values.

class EnvironmentInfo(TypedDict):
    environment_id: str
    name: str
    properties: Dict[str, Any]
    agents_present: List[str]

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Multi-agent simulation environment state.
        """

        # Agents: {agent_id: AgentInfo}
        # Represents all agents and their states.
        self.agents: Dict[str, AgentInfo] = {}

        # Environments: {environment_id: EnvironmentInfo}
        # Represents all simulation spaces/worlds.
        self.environments: Dict[str, EnvironmentInfo] = {}

        # --- Constraints ---
        # - An agent can only occupy one position in one environment at a time.
        # - Actions executed by agents may change both their own and others’ states or knowledge.
        # - Knowledge updates for an agent are persistent and may reference other agents’ actions.
        # - An agent must exist within a valid environment to perform position or action updates.

    def get_agent_info(self, agent_id: str) -> dict:
        """
        Retrieve detailed information (position, environment, action, knowledge base)
        for a specified agent.

        Args:
            agent_id (str): The unique identifier of the agent.

        Returns:
            dict:
                {"success": True, "data": AgentInfo}
                or
                {"success": False, "error": "Agent does not exist"}

        Constraints:
            - The specified agent must exist in the simulation environment.
        """
        agent = self.agents.get(agent_id)
        if not agent:
            return {"success": False, "error": "Agent does not exist"}
        return {"success": True, "data": agent}

    def get_agents_in_environment(self, environment_id: str) -> dict:
        """
        List all agent IDs currently present in the specified environment.

        Args:
            environment_id (str): The identifier of the environment to query.

        Returns:
            dict: {
                "success": True,
                "data": List[str],  # List of agent IDs in the environment (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Description of the error (environment does not exist)
            }

        Constraints:
            - The provided environment_id must exist in the simulation environment.
        """
        env = self.environments.get(environment_id)
        if env is None:
            return { "success": False, "error": "Environment does not exist" }
        return { "success": True, "data": list(env["agents_present"]) }

    def get_environment_info(self, environment_id: str) -> dict:
        """
        Retrieve full details (name, properties, agents) about a specified environment.

        Args:
            environment_id (str): Unique identifier of the environment to retrieve.

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "data": EnvironmentInfo  # Complete environment info
                }
                On failure: {
                    "success": False,
                    "error": "Environment does not exist"
                }
        Constraints:
            - The environment must exist. If not, returns error.
        """
        if environment_id not in self.environments:
            return { "success": False, "error": "Environment does not exist" }
        return { "success": True, "data": self.environments[environment_id] }

    def get_agent_position(self, agent_id: str) -> dict:
        """
        Query the current position and environment of a specified agent.

        Args:
            agent_id (str): The unique identifier of the agent.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "position": str,
                    "environment_id": str
                }
            }
            OR
            {
                "success": False,
                "error": str  # If agent_id does not exist.
            }

        Constraints:
            - agent_id must exist in the environment.
        """
        agent = self.agents.get(agent_id)
        if not agent:
            return {"success": False, "error": "Agent does not exist."}
        return {
            "success": True,
            "data": {
                "position": agent["position"],
                "environment_id": agent["environment_id"]
            }
        }

    def get_agent_knowledge_base(self, agent_id: str) -> dict:
        """
        Retrieve the knowledge base of an agent.

        Args:
            agent_id (str): The unique identifier of the agent.

        Returns:
            dict: {
                "success": True,
                "data": Dict[str, Any]  # The agent's knowledge base
            }
            or
            {
                "success": False,
                "error": str  # Error description if agent does not exist
            }

        Constraints:
            - The agent with agent_id must exist in the environment.
        """
        agent = self.agents.get(agent_id)
        if agent is None:
            return { "success": False, "error": "Agent does not exist" }
        return { "success": True, "data": agent["knowledge_base"] }

    def list_all_agents(self) -> dict:
        """
        Return IDs and summary information for all agents in the simulation.

        Returns:
            dict: {
                "success": True,
                "data": List[AgentInfo],  # List of agent summaries, or empty if none
            }

        Notes:
            - This method does not filter or exclude any agents.
            - All agent attributes as defined in AgentInfo are returned.
        """
        agents_list = list(self.agents.values())
        return { "success": True, "data": agents_list }

    def list_all_environments(self) -> dict:
        """
        List all simulation environments with their associated properties.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[EnvironmentInfo]
            }
            - If no environments exist, "data" is an empty list.
        """
        all_envs = list(self.environments.values())
        return {
            "success": True,
            "data": all_envs
        }

    def move_agent(self, agent_id: str, new_environment_id: str, new_position: str) -> dict:
        """
        Relocate a single agent to a new position in a specified environment.

        Args:
            agent_id (str): The unique id of the agent to move.
            new_environment_id (str): The id of the target environment.
            new_position (str): The new position of the agent within the environment.

        Returns:
            dict: {
                "success": True,
                "message": "Agent <agent_id> moved to <new_position> in environment <new_environment_id>"
            }
            or
            {
                "success": False,
                "error": str
            }
        Constraints:
            - Agent must exist.
            - Environment must exist.
            - An agent can only occupy one position in one environment at a time.
            - The agent will only be present in the new environment after completion.
        """
        if agent_id not in self.agents:
            return { "success": False, "error": f"Agent '{agent_id}' does not exist." }
        if new_environment_id not in self.environments:
            return { "success": False, "error": f"Environment '{new_environment_id}' does not exist." }

        agent_info = self.agents[agent_id]
        prev_env_id = agent_info["environment_id"]

        # Remove agent from previous environment's agents_present list if present and different environment
        if prev_env_id in self.environments and agent_id in self.environments[prev_env_id]['agents_present']:
            if prev_env_id != new_environment_id:
                self.environments[prev_env_id]['agents_present'].remove(agent_id)

        # Add to new environment's agents_present if not already present
        if agent_id not in self.environments[new_environment_id]['agents_present']:
            self.environments[new_environment_id]['agents_present'].append(agent_id)

        # Update agent's location and environment
        agent_info["environment_id"] = new_environment_id
        agent_info["position"] = new_position
        self.agents[agent_id] = agent_info

        return {
            "success": True,
            "message": f"Agent {agent_id} moved to {new_position} in environment {new_environment_id}"
        }

    def move_agents_batch(self, environment_id: str, agents_positions: list) -> dict:
        """
        Relocate multiple agents to new positions in the specified environment in one batch operation.

        Args:
            environment_id (str): The ID of the environment to move agents to.
            agents_positions (List[Dict[str, str]]): Each dict contains:
                - 'agent_id': str, the ID of the agent to move,
                - 'position': str, the new position in the environment.

        Returns:
            dict: 
                Success: { "success": True, "message": "Moved N agents to environment <environment_id>." }
                Failure: { "success": False, "error": "reason" }

        Constraints:
            - The environment_id must exist.
            - Each agent_id must exist.
            - Each agent can only be referenced once in the batch.
            - Agents are updated atomically (all or none).
            - Updates agents' position and environment_id and updates agents_present in environments.
        """
        # Validate environment exists
        if environment_id not in self.environments:
            return {"success": False, "error": "Target environment does not exist."}
    
        # Check for duplicate agent_ids in agents_positions
        seen_agents = set()
        for entry in agents_positions:
            agent_id = entry.get("agent_id")
            if agent_id in seen_agents:
                return {"success": False, "error": f"Duplicate agent_id '{agent_id}' in input."}
            seen_agents.add(agent_id)
    
        # Pre-validate all agent_ids
        agent_id_list = [entry.get("agent_id") for entry in agents_positions]
        for agent_id in agent_id_list:
            if agent_id not in self.agents:
                return {"success": False, "error": f"Agent '{agent_id}' does not exist."}

        # Store prior environments and agents_present for atomicity (deep copy not strictly needed as we don't mutate yet)
        old_environments = {}
        for agent_id in agent_id_list:
            old_env_id = self.agents[agent_id]["environment_id"]
            if old_env_id not in old_environments:
                old_environments[old_env_id] = set(self.environments[old_env_id]["agents_present"])

        # Now apply updates
        # Track for final update: which envs should have agents removed/added
        to_remove = {}  # {old_env_id: set(agent_ids)}
        to_add = set()  # agent_ids to add to new env
    
        for entry in agents_positions:
            agent_id = entry["agent_id"]
            new_position = entry["position"]
            old_env_id = self.agents[agent_id]["environment_id"]
            # Mark for removal from old env
            if old_env_id != environment_id:
                to_remove.setdefault(old_env_id, set()).add(agent_id)
                to_add.add(agent_id)
            elif agent_id not in self.environments[environment_id]["agents_present"]:
                # Same env but agent is not present (should not happen, but fix)
                to_add.add(agent_id)

        # Remove agents from their old envs' agents_present
        for old_env_id, agent_set in to_remove.items():
            for agent_id in agent_set:
                if agent_id in self.environments[old_env_id]["agents_present"]:
                    self.environments[old_env_id]["agents_present"].remove(agent_id)
    
        # Add agents to new env's agents_present (avoid duplicates)
        for agent_id in agent_id_list:
            if agent_id not in self.environments[environment_id]["agents_present"]:
                self.environments[environment_id]["agents_present"].append(agent_id)
    
        # Update agent's environment_id and position
        for entry in agents_positions:
            agent_id = entry["agent_id"]
            new_position = entry["position"]
            self.agents[agent_id]["position"] = new_position
            self.agents[agent_id]["environment_id"] = environment_id

        return {
            "success": True, 
            "message": f"Moved {len(agent_id_list)} agents to environment {environment_id}."
        }

    def set_agent_action(self, agent_id: str, action: str) -> dict:
        """
        Set or update the current_action for the specified agent.

        Args:
            agent_id (str): Unique identifier of the agent.
            action (str): Action string to set (e.g., 'Inspect').

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Agent <agent_id> action set to <action>"
                    }
                On error:
                    {
                        "success": False,
                        "error": <reason>
                    }
        Constraints:
            - Agent must exist.
            - Agent must be assigned to a valid environment.
        """
        agent = self.agents.get(agent_id)
        if not agent:
            return {"success": False, "error": f"Agent '{agent_id}' does not exist"}

        env_id = agent.get("environment_id")
        if not env_id or env_id not in self.environments:
            return {"success": False, "error": f"Agent '{agent_id}' does not belong to a valid environment"}

        agent["current_action"] = action
        return {
            "success": True,
            "message": f"Agent '{agent_id}' action set to '{action}'"
        }

    def update_agent_knowledge_base(self, agent_id: str, knowledge_updates: Dict[str, Any]) -> dict:
        """
        Add or modify entries in the specified agent's knowledge base.
        Supports references to other agents' actions/events (keys/values are flexible).

        Args:
            agent_id (str): The ID of the agent whose knowledge base is being updated.
            knowledge_updates (Dict[str, Any]): Key-value pairs to update/add in the knowledge base.

        Returns:
            dict: {
                "success": True,
                "message": "Agent knowledge base updated."
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - Agent must exist.
            - Agent must exist within a valid environment (its environment_id in self.environments).
            - Updates are persistent (merged into current knowledge_base).
            - No exception raised on missing/extra keys: all are allowed.
        """
        # Check agent existence
        agent = self.agents.get(agent_id)
        if not agent:
            return { "success": False, "error": "Agent does not exist" }
    
        env_id = agent.get("environment_id")
        if env_id not in self.environments:
            return { "success": False, "error": "Agent is not in a valid environment" }
    
        if not isinstance(knowledge_updates, dict):
            return { "success": False, "error": "knowledge_updates must be a dictionary" }

        # Update (merge) knowledge base
        agent["knowledge_base"].update(knowledge_updates)

        return { "success": True, "message": "Agent knowledge base updated." }

    def batch_update_agent_knowledge(self, updates: list) -> dict:
        """
        Apply multiple knowledge updates to one or more agents atomically.

        Args:
            updates (list): List of dicts, each with:
                - 'agent_id' (str): Target agent's ID.
                - 'knowledge_update' (dict): Key-value pairs to merge into agent's knowledge_base.

        Returns:
            dict:
                - On success:
                    { "success": True, "message": "Successfully updated knowledge base for N agent(s)" }
                - On failure:
                    { "success": False, "error": str }
    
        Constraints:
            - All specified agent_ids must exist; operation fails if any invalid.
            - Each 'knowledge_update' must be a dict.
            - Updates are persistent (write-through).
        """
        if not isinstance(updates, list):
            return { "success": False, "error": "Input 'updates' must be a list" }

        invalid_entries = []
        for i, entry in enumerate(updates):
            # Basic structure/type checks
            if not isinstance(entry, dict):
                invalid_entries.append(f"entry #{i} not a dict")
                continue
            agent_id = entry.get("agent_id")
            knowledge_update = entry.get("knowledge_update")
            if agent_id is None or agent_id not in self.agents:
                invalid_entries.append(f"entry #{i}: invalid or missing agent_id '{agent_id}'")
                continue
            if not isinstance(knowledge_update, dict):
                invalid_entries.append(f"entry #{i}: knowledge_update must be a dict")
                continue

        if invalid_entries:
            return { "success": False, "error": f"Invalid entries: {', '.join(invalid_entries)}" }

        # Apply updates
        for entry in updates:
            agent_id = entry["agent_id"]
            knowledge_update = entry["knowledge_update"]
            self.agents[agent_id]["knowledge_base"].update(knowledge_update)

        return { 
            "success": True, 
            "message": f"Successfully updated knowledge base for {len(updates)} agent(s)"
        }

    def create_agent(
        self,
        agent_id: str,
        environment_id: str,
        position: str,
        current_action: str = "",
        knowledge_base: dict = None
    ) -> dict:
        """
        Add a new agent to the simulation in a given environment and position.

        Args:
            agent_id (str): Unique identifier for the new agent.
            environment_id (str): The environment where the agent should be placed.
            position (str): The initial position for the agent in the environment.
            current_action (str, optional): Initial action of the agent. Defaults to "".
            knowledge_base (dict, optional): Initial knowledge base for the agent. Defaults to {}.

        Returns:
            dict: {
                "success": True,
                "message": str
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - agent_id must be unique in the system.
            - environment_id must refer to a valid existing environment.
            - Agent added to agents dict and to the environment's agents_present list.
        """
        if agent_id in self.agents:
            return { "success": False, "error": "Agent ID already exists." }
        if environment_id not in self.environments:
            return { "success": False, "error": "Environment does not exist." }

        if knowledge_base is None:
            knowledge_base = {}

        agent_info: AgentInfo = {
            "agent_id": agent_id,
            "position": position,
            "environment_id": environment_id,
            "current_action": current_action,
            "knowledge_base": knowledge_base
        }
        self.agents[agent_id] = agent_info

        # Add agent to the environment's agents_present list
        if "agents_present" not in self.environments[environment_id]:
            self.environments[environment_id]["agents_present"] = []
        if agent_id not in self.environments[environment_id]["agents_present"]:
            self.environments[environment_id]["agents_present"].append(agent_id)

        return {
            "success": True,
            "message": f"Agent {agent_id} created in environment {environment_id} at position {position}."
        }

    def remove_agent(self, agent_id: str) -> dict:
        """
        Remove an agent from the simulation, including state and knowledge cleanup.

        Args:
            agent_id (str): The unique identifier of the agent to be removed.

        Returns:
            dict: {
                "success": True,
                "message": "Agent <agent_id> removed from simulation."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - Agent must exist in the simulation.
            - Agent is removed from self.agents and from its environment's agents_present list.
        """
        if agent_id not in self.agents:
            return {"success": False, "error": f"Agent '{agent_id}' does not exist."}

        # Remove the agent from every environment presence list.
        for env_info in self.environments.values():
            if agent_id in env_info.get('agents_present', []):
                env_info['agents_present'].remove(agent_id)

        # Remove the agent from the simulation
        del self.agents[agent_id]

        return {"success": True, "message": f"Agent '{agent_id}' removed from simulation."}

    def add_agent_to_environment(self, agent_id: str, environment_id: str) -> dict:
        """
        Adds an existing agent to the specified environment's presence list, enabling multi-environment
        placement (agent can be 'present' in several environments simultaneously, but only one is its primary
        state environment at any time).

        Args:
            agent_id (str): The identifier of the agent to add.
            environment_id (str): The identifier of the environment to which to add the agent.

        Returns:
            dict: {
                "success": True,
                "message": "Agent <agent_id> added to environment <environment_id>"
            }
            or (on error):
            dict: {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - Agent and environment must both exist.
            - Agent may already be in the environment; operation is idempotent.
            - Does NOT change the agent's own environment_id or position.
        """
        if agent_id not in self.agents:
            return { "success": False, "error": f"Agent '{agent_id}' does not exist" }
        if environment_id not in self.environments:
            return { "success": False, "error": f"Environment '{environment_id}' does not exist" }

        env_info = self.environments[environment_id]
        if agent_id not in env_info["agents_present"]:
            env_info["agents_present"].append(agent_id)
            # Optionally sort or keep unique, but append is sufficient here.

        return {
            "success": True,
            "message": f"Agent {agent_id} added to environment {environment_id}"
        }

    def remove_agent_from_environment(self, agent_id: str) -> dict:
        """
        Remove an agent from their current environment (for agent deactivation).

        Args:
            agent_id (str): The ID of the agent to remove from its environment.

        Returns:
            dict: {
                "success": True,
                "message": "Agent <agent_id> removed from environment <environment_id>."
            } on success,
            or
            {
                "success": False,
                "error": "reason"
            } on error.

        Constraints:
            - The agent must exist.
            - The agent must currently be in a valid environment to be removed from it.
            - After removal, the agent's `environment_id` will be set to an empty string to indicate it is not in any environment.
        """
        agent = self.agents.get(agent_id)
        if not agent:
            return { "success": False, "error": f"Agent '{agent_id}' does not exist." }

        current_env_id = agent.get("environment_id")
        if not current_env_id:
            return { "success": False, "error": f"Agent '{agent_id}' is not in any environment." }

        env = self.environments.get(current_env_id)
        if not env:
            # This should not happen, but handle gracefully
            agent["environment_id"] = ""
            return {
                "success": False,
                "error": f"Environment '{current_env_id}' does not exist; agent '{agent_id}' marked as not in any environment."
            }

        # Remove agent from environment's agents_present list if present
        if agent_id in env["agents_present"]:
            env["agents_present"].remove(agent_id)

        # Update agent's environment_id to indicate it is not in any environment
        agent["environment_id"] = ""

        return {
            "success": True,
            "message": f"Agent '{agent_id}' removed from environment '{current_env_id}'."
        }


class MultiAgentSimulationEnvironment(BaseEnv):
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

    def get_agent_info(self, **kwargs):
        return self._call_inner_tool('get_agent_info', kwargs)

    def get_agents_in_environment(self, **kwargs):
        return self._call_inner_tool('get_agents_in_environment', kwargs)

    def get_environment_info(self, **kwargs):
        return self._call_inner_tool('get_environment_info', kwargs)

    def get_agent_position(self, **kwargs):
        return self._call_inner_tool('get_agent_position', kwargs)

    def get_agent_knowledge_base(self, **kwargs):
        return self._call_inner_tool('get_agent_knowledge_base', kwargs)

    def list_all_agents(self, **kwargs):
        return self._call_inner_tool('list_all_agents', kwargs)

    def list_all_environments(self, **kwargs):
        return self._call_inner_tool('list_all_environments', kwargs)

    def move_agent(self, **kwargs):
        return self._call_inner_tool('move_agent', kwargs)

    def move_agents_batch(self, **kwargs):
        return self._call_inner_tool('move_agents_batch', kwargs)

    def set_agent_action(self, **kwargs):
        return self._call_inner_tool('set_agent_action', kwargs)

    def update_agent_knowledge_base(self, **kwargs):
        return self._call_inner_tool('update_agent_knowledge_base', kwargs)

    def batch_update_agent_knowledge(self, **kwargs):
        return self._call_inner_tool('batch_update_agent_knowledge', kwargs)

    def create_agent(self, **kwargs):
        return self._call_inner_tool('create_agent', kwargs)

    def remove_agent(self, **kwargs):
        return self._call_inner_tool('remove_agent', kwargs)

    def add_agent_to_environment(self, **kwargs):
        return self._call_inner_tool('add_agent_to_environment', kwargs)

    def remove_agent_from_environment(self, **kwargs):
        return self._call_inner_tool('remove_agent_from_environment', kwargs)
