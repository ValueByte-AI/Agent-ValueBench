# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import time
import re



# Advertiser entity
class AdvertiserInfo(TypedDict):
    advertiser_id: str
    name: str
    industry: str
    profile_data: dict  # could be more specific

# Agent entity
class AgentInfo(TypedDict):
    agent_id: str
    name: str
    expertise: str
    availability: bool
    assigned_advertiser_id: str  # could become a List[str] if multiple, but spec says "id"

# Campaign entity
class CampaignInfo(TypedDict):
    campaign_id: str
    advertiser_id: str
    objective: str
    budget: float
    status: str

# Recommendation entity
class RecommendationInfo(TypedDict):
    advertiser_id: str
    recommended_agent_ids: List[str]
    timestamp: str
    recommendation_reasoning: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        The environment for digital advertising management, tracking advertisers, agents, campaigns, and recommendations.
        """

        # Advertisers: {advertiser_id: AdvertiserInfo}
        self.advertisers: Dict[str, AdvertiserInfo] = {}

        # Agents: {agent_id: AgentInfo}
        self.agents: Dict[str, AgentInfo] = {}

        # Campaigns: {campaign_id: CampaignInfo}
        self.campaigns: Dict[str, CampaignInfo] = {}

        # Recommendations: {advertiser_id: RecommendationInfo}
        self.recommendations: Dict[str, RecommendationInfo] = {}

        # Historical recommendations: {advertiser_id: List[RecommendationInfo]}
        self.recommendation_history: Dict[str, List[RecommendationInfo]] = {}

        # --- Constraints (to enforce in future methods) ---
        # - Each agent can only be assigned to a limited number of advertisers at a time (based on availability).
        # - Recommendations should align agent expertise with advertiser's industry or campaign objectives.
        # - Only agents with availability = True are considered for recommendations.
        # - Assignment of agents must respect existing advertiser-agent exclusivity or preference constraints.

    def get_advertiser_by_id(self, advertiser_id: str) -> dict:
        """
        Retrieve advertiser details using advertiser_id.

        Args:
            advertiser_id (str): The unique identifier for the advertiser.

        Returns:
            dict:
                If advertiser exists:
                    {
                        "success": True,
                        "data": AdvertiserInfo
                    }
                If advertiser does not exist:
                    {
                        "success": False,
                        "error": "Advertiser not found"
                    }

        Constraints:
            - The advertiser_id must exist in the platform.
        """
        advertiser = self.advertisers.get(advertiser_id)
        if advertiser is None:
            return { "success": False, "error": "Advertiser not found" }
        return { "success": True, "data": advertiser }

    def list_advertisers(self) -> dict:
        """
        Return a list of all advertisers in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[AdvertiserInfo]  # possibly empty list if no advertisers
            }
            or
            {
                "success": False,
                "error": str  # Description of problem fetching advertisers
            }

        Constraints:
            - No input required.
            - Always returns all advertisers in the system.
            - Result list may be empty but that is not an error.
        """
        if not isinstance(self.advertisers, dict):
            return { "success": False, "error": "Internal error: advertiser data missing or corrupted." }

        advertiser_list = list(self.advertisers.values())
        return { "success": True, "data": advertiser_list }

    def get_agent_by_id(self, agent_id: str) -> dict:
        """
        Retrieve agent details for a given agent_id.

        Args:
            agent_id (str): The unique identifier of the agent.

        Returns:
            dict: 
                - If agent exists: { "success": True, "data": AgentInfo }
                - If agent does not exist: { "success": False, "error": "Agent not found" }
        Constraints:
            - agent_id must exist in self.agents.
        """
        agent = self.agents.get(agent_id)
        if agent is None:
            return {"success": False, "error": "Agent not found"}
        return {"success": True, "data": agent}

    def list_agents(self) -> dict:
        """
        Return a list of all agents, each with their expertise, availability, and current assignment(s).

        Returns:
            dict: 
                {
                    "success": True,
                    "data": List[AgentInfo],  # all agents in system (possibly empty)
                }
        """
        # Return all agent records as a list
        return {
            "success": True,
            "data": list(self.agents.values())
        }

    def get_agents_by_expertise(self, expertise: str) -> dict:
        """
        Retrieve all agents whose expertise matches the specified area.

        Args:
            expertise (str): The expertise area to filter agents by.

        Returns:
            dict: {
                "success": True,
                "data": List[AgentInfo]  # List of agent info dicts that match the expertise
            }
            OR
            {
                "success": False,
                "error": str  # Error description if input invalid
            }

        Constraints:
            - 'expertise' parameter must be a non-empty string.
        """
        if not isinstance(expertise, str) or not expertise.strip():
            return {"success": False, "error": "Expertise area must be a non-empty string."}

        expertise = expertise.strip()
        result = [
            agent for agent in self.agents.values()
            if agent.get("expertise") == expertise
        ]

        return {"success": True, "data": result}

    def get_available_agents(self) -> dict:
        """
        List all agents that are currently marked as available.

        Returns:
            dict: {
                "success": True,
                "data": List[AgentInfo],  # List of agent records with availability == True (may be empty if none)
            }

        Constraints:
            - Only agents with availability == True are included.
            - No parameters needed; this is a full-platform query.
        """
        available_agents = [
            agent_info
            for agent_info in self.agents.values()
            if agent_info.get("availability", False) is True
        ]
        return {
            "success": True,
            "data": available_agents
        }

    def get_assigned_agents_for_advertiser(self, advertiser_id: str) -> dict:
        """
        Retrieve all agents currently assigned to the specified advertiser.

        Args:
            advertiser_id (str): The ID of the advertiser.

        Returns:
            dict: {
                "success": True,
                "data": List[AgentInfo],  # List of agents assigned to advertiser (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. advertiser does not exist
            }

        Constraints:
            - advertiser_id must exist in the system.
            - Returns all agents where assigned_advertiser_id == advertiser_id.
        """
        if advertiser_id not in self.advertisers:
            return { "success": False, "error": "Advertiser does not exist" }

        result = [
            agent_info
            for agent_info in self.agents.values()
            if agent_info.get("assigned_advertiser_id") == advertiser_id
        ]

        return { "success": True, "data": result }

    def get_advertiser_campaigns(self, advertiser_id: str) -> dict:
        """
        List all campaigns associated with a given advertiser.

        Args:
            advertiser_id (str): The unique identifier for the advertiser.

        Returns:
            dict: {
                "success": True,
                "data": List[CampaignInfo]  # May be empty if no campaigns
            }
            or
            {
                "success": False,
                "error": str  # Reason why operation could not be performed
            }

        Constraints:
            - advertiser_id must exist in the system.
        """
        if advertiser_id not in self.advertisers:
            return {"success": False, "error": "Advertiser ID does not exist"}

        matched_campaigns = [
            campaign for campaign in self.campaigns.values()
            if campaign["advertiser_id"] == advertiser_id
        ]

        return {"success": True, "data": matched_campaigns}

    def get_campaign_by_id(self, campaign_id: str) -> dict:
        """
        Retrieve campaign details for a specific campaign_id.

        Args:
            campaign_id (str): The unique identifier of the campaign.

        Returns:
            dict:
                On success:
                    {"success": True, "data": CampaignInfo}
                On failure (not found):
                    {"success": False, "error": "Campaign not found"}

        Constraints:
            - campaign_id must exist in the platform's campaign records.
        """
        campaign = self.campaigns.get(campaign_id)
        if campaign is None:
            return {"success": False, "error": "Campaign not found"}
        return {"success": True, "data": campaign}

    def get_recommendation_by_advertiser(self, advertiser_id: str) -> dict:
        """
        Retrieve the current or most recent agent recommendations for the given advertiser.

        Args:
            advertiser_id (str): The ID of the advertiser.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": RecommendationInfo
                }
                or
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - Advertiser must exist.
            - Recommendation must exist for this advertiser.
        """
        if advertiser_id not in self.advertisers:
            return { "success": False, "error": "Advertiser does not exist" }
        if advertiser_id not in self.recommendations:
            return { "success": False, "error": "No recommendation found for this advertiser" }
        return {
            "success": True,
            "data": self.recommendations[advertiser_id]
        }

    def get_recommendation_history(self, advertiser_id: str) -> dict:
        """
        Retrieve the historical record of agent recommendations for a given advertiser.

        Args:
            advertiser_id (str): The ID of the advertiser whose recommendation history is requested.

        Returns:
            dict: {
                "success": True,
                "data": List[RecommendationInfo]  # List of historical recommendations (can be empty)
            }
            OR
            {
                "success": False,
                "error": str  # e.g., "Advertiser does not exist"
            }

        Constraints:
            - The advertiser_id must exist in the platform.
            - If no history is found for the advertiser, return an empty list (success).
        """
        if advertiser_id not in self.advertisers:
            return {"success": False, "error": "Advertiser does not exist"}

        history: List[RecommendationInfo] = []
        raw_history = getattr(self, "recommendation_history", None)

        if isinstance(raw_history, dict):
            candidate = raw_history.get(advertiser_id, [])
            history.extend(self._coerce_history_entries(advertiser_id, candidate))
        elif isinstance(raw_history, str):
            history.extend(self._extract_history_entries_from_text(advertiser_id, raw_history))

        current_recommendation = self.recommendations.get(advertiser_id)
        if isinstance(current_recommendation, dict):
            history.append(copy.deepcopy(current_recommendation))

        return {"success": True, "data": history}

    def _build_history_entry(self, advertiser_id: str, text: str, timestamp: str = "historical") -> RecommendationInfo:
        agent_ids = []
        for match in re.findall(r"\b(?:AGT|agt)[-_]?\d+\b", text):
            if match not in agent_ids:
                agent_ids.append(match)

        return {
            "advertiser_id": advertiser_id,
            "recommended_agent_ids": agent_ids,
            "timestamp": timestamp,
            "recommendation_reasoning": text.strip(),
        }

    def _coerce_history_entries(self, advertiser_id: str, candidate: Any) -> List[RecommendationInfo]:
        if isinstance(candidate, list):
            return [copy.deepcopy(entry) for entry in candidate if isinstance(entry, dict)]
        if isinstance(candidate, dict):
            return [copy.deepcopy(candidate)]
        if isinstance(candidate, str):
            stripped = candidate.strip()
            if not stripped or stripped.lower() == "no prior history.":
                return []
            return [self._build_history_entry(advertiser_id, stripped)]
        return []

    def _extract_history_entries_from_text(self, advertiser_id: str, raw_text: str) -> List[RecommendationInfo]:
        if not raw_text.strip():
            return []

        entries: List[RecommendationInfo] = []

        record_pattern = re.compile(
            r"Record for\s+([A-Za-z0-9_-]+)\s*:\s*(.*?)(?=(?:Record for\s+[A-Za-z0-9_-]+\s*:)|$)",
            re.IGNORECASE | re.DOTALL,
        )
        line_pattern = re.compile(r"^\s*-\s*([A-Za-z0-9_-]+)\s*:\s*(.+)$", re.MULTILINE)

        for pattern in (record_pattern, line_pattern):
            for match in pattern.finditer(raw_text):
                record_advertiser_id = match.group(1)
                record_text = match.group(2).strip()
                if record_advertiser_id.lower() != advertiser_id.lower():
                    continue
                if not record_text or "no prior history" in record_text.lower():
                    return []
                timestamp_match = re.search(r"\b\d{4}-\d{2}-\d{2}(?:[T ][0-9:]+Z?)?\b", record_text)
                timestamp = timestamp_match.group(0) if timestamp_match else "historical"
                entries.append(self._build_history_entry(advertiser_id, record_text, timestamp=timestamp))

            if entries:
                return entries

        # Fallback for compact single-advertiser free text such as repeated yearly notes.
        if advertiser_id.lower() in raw_text.lower() and "no prior history" not in raw_text.lower():
            return [self._build_history_entry(advertiser_id, raw_text.strip())]
        if len(self.advertisers) == 1 and advertiser_id in self.advertisers and "no prior history" not in raw_text.lower():
            return [self._build_history_entry(advertiser_id, raw_text.strip())]

        return []

    def check_agent_availability(self, agent_id: str) -> dict:
        """
        Query whether an agent's availability is True and return the number of current assignments.

        Args:
            agent_id (str): The unique ID of the agent to check.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "availability": bool,
                    "assignment_count": int   # 0 if not assigned, 1 if assigned (per current schema)
                }
            }
            or
            {
                "success": False,
                "error": str  # Error message if agent does not exist
            }

        Constraints:
            - If agent is not assigned ('assigned_advertiser_id' is empty string or None), assignment_count is 0.
            - If agent is assigned, assignment_count is 1 (per class attribute definition).
        """
        agent = self.agents.get(agent_id)
        if not agent:
            return {"success": False, "error": "Agent not found"}

        assigned_adv = agent.get("assigned_advertiser_id")
        # Account for possible None or empty string assignments
        if assigned_adv and str(assigned_adv).strip():
            assignment_count = 1
        else:
            assignment_count = 0

        return {
            "success": True,
            "data": {
                "availability": agent.get("availability", False),
                "assignment_count": assignment_count
            }
        }

    def check_agent_assignment_limit(self, agent_id: str) -> dict:
        """
        Check if an agent has reached their assignment limit.
    
        Args:
            agent_id (str): The ID of the agent to check.
        
        Returns:
            dict: {
                "success": True,
                "limit_reached": bool,    # True if agent is at assignment limit
                "current_assignments": int,  # Number of advertisers currently assigned
                "max_assignments": int       # Maximum allowed assignments (here, 1)
            }
            OR
            {
                "success": False,
                "error": str  # Reason agent not checked (not found)
            }
        Constraints:
            - Each agent can only be assigned to one advertiser at a time.
        """
        agent = self.agents.get(agent_id)
        if not agent:
            return { "success": False, "error": "Agent not found" }
    
        # For current schema, assignment limit is 1
        max_assignments = 1
        current_assignments = 1 if agent.get("assigned_advertiser_id") else 0
        limit_reached = current_assignments >= max_assignments
    
        return {
            "success": True,
            "limit_reached": limit_reached,
            "current_assignments": current_assignments,
            "max_assignments": max_assignments
        }

    def check_advertiser_agent_exclusivity(self, advertiser_id: str, agent_id: str) -> dict:
        """
        Check if exclusivity or preference constraints apply between a given advertiser and agent.

        Args:
            advertiser_id (str): The ID of the advertiser.
            agent_id (str): The ID of the agent.

        Returns:
            dict:
                - success (bool)
                - data (dict: {'is_exclusive': bool, 'details': str}) if check performed successfully
                - error (str) if check failed

        Constraints:
            - Both advertiser and agent must exist.
            - Agent assignment is exclusive: if agent is already assigned to another advertiser, exclusivity applies.
            - No custom preference/exclusivity logic is encoded unless additional data structures are later added.
        """
        if advertiser_id not in self.advertisers:
            return {"success": False, "error": "Advertiser does not exist"}
        if agent_id not in self.agents:
            return {"success": False, "error": "Agent does not exist"}

        agent_info = self.agents[agent_id]
        assigned_advertiser = agent_info.get("assigned_advertiser_id")

        if assigned_advertiser and assigned_advertiser != advertiser_id:
            return {
                "success": True,
                "data": {
                    "is_exclusive": True,
                    "details": f"Agent {agent_id} is exclusively assigned to advertiser {assigned_advertiser}."
                }
            }
        # If agent is assigned to this advertiser, or not assigned to any, no exclusivity constraint blocks the assignment
        return {
            "success": True,
            "data": {
                "is_exclusive": False,
                "details": "No exclusivity or preference constraints block assignment between this advertiser and agent."
            }
        }

    def match_agents_for_advertiser(self, advertiser_id: str) -> dict:
        """
        Query which available agents are suitable for an advertiser, based on expertise, availability, and constraints.

        Args:
            advertiser_id (str): The ID of the advertiser for whom to match agents.

        Returns:
            dict: {
                "success": True,
                "data": List[AgentInfo],  # All agents suitable for this advertiser
            }
            or
            {
                "success": False,
                "error": str  # Reason for error (e.g., advertiser does not exist)
            }

        Constraints:
            - Only agents with availability == True are considered.
            - Agent's expertise must match advertiser's industry.
            - Agent must not currently be assigned to another advertiser (if so, skip).
            - Any exclusivity constraints must be respected (with current model: only one assignment).
        """
        # Advertiser must exist
        if advertiser_id not in self.advertisers:
            return { "success": False, "error": "Advertiser does not exist" }

        advertiser = self.advertisers[advertiser_id]
        advertiser_industry = advertiser.get("industry", "")

        suitable_agents = []
        for agent in self.agents.values():
            # Only available
            if not agent.get("availability", False):
                continue
            # Only agents whose expertise matches advertiser's industry
            if agent.get("expertise", "") != advertiser_industry:
                continue
            # Only agents not assigned to another advertiser
            assigned_advertiser_id = agent.get("assigned_advertiser_id", "")
            # If not assigned, or assigned to this advertiser (could allow re-matching to same advertiser)
            if assigned_advertiser_id and assigned_advertiser_id != advertiser_id:
                continue
            # Additional exclusivity or assignment limit rules would go here.
            suitable_agents.append(agent)

        return { "success": True, "data": suitable_agents }

    def assign_agent_to_advertiser(self, agent_id: str, advertiser_id: str) -> dict:
        """
        Assigns an available agent to an advertiser, respecting assignment limits and exclusivity/preference constraints.

        Args:
            agent_id (str): The agent's identifier.
            advertiser_id (str): The advertiser's identifier.

        Returns:
            dict: {
                "success": True,
                "message": "Agent <id> assigned to advertiser <id>"
            }
            or
            {
                "success": False,
                "error": <description>
            }

        Constraints:
            - Agent must exist.
            - Advertiser must exist.
            - Agent must be available (availability=True).
            - Agent can only be assigned to one advertiser at a time (if assigned_advertiser_id not empty/None).
            - Must respect exclusivity (no conflicting assignment).
        """
        # Check if agent exists
        if agent_id not in self.agents:
            return {"success": False, "error": "Agent does not exist"}

        # Check if advertiser exists
        if advertiser_id not in self.advertisers:
            return {"success": False, "error": "Advertiser does not exist"}

        agent = self.agents[agent_id]

        # Check agent availability
        if not agent["availability"]:
            return {"success": False, "error": "Agent is not available for assignment"}

        # Check assignment/exclusivity
        existing_assignment = agent.get("assigned_advertiser_id")
        if existing_assignment and existing_assignment != "" and existing_assignment != advertiser_id:
            return {"success": False, "error": "Agent is already assigned to a different advertiser"}

        # Assignment state and availability are modeled separately.
        # This tool only changes the current advertiser assignment.
        agent["assigned_advertiser_id"] = advertiser_id

        # Save back (dict is mutable, but for clarity)
        self.agents[agent_id] = agent

        return {
            "success": True,
            "message": f"Agent {agent_id} assigned to advertiser {advertiser_id}"
        }

    def unassign_agent_from_advertiser(self, agent_id: str, advertiser_id: str) -> dict:
        """
        Remove an agent’s assignment from a given advertiser.
    
        Args:
            agent_id (str): The ID of the agent to unassign.
            advertiser_id (str): The ID of the advertiser to remove the assignment from.

        Returns:
            dict: {
                "success": True,
                "message": "Agent <id> unassigned from advertiser <id>."
            }
            or
            {
                "success": False,
                "error": <reason>
            }
    
        Constraints:
            - Agent and advertiser must both exist.
            - Agent must be assigned to the specified advertiser.
        """
        # Check agent existence
        agent = self.agents.get(agent_id)
        if not agent:
            return {"success": False, "error": "Agent does not exist."}
    
        # Check advertiser existence
        if advertiser_id not in self.advertisers:
            return {"success": False, "error": "Advertiser does not exist."}

        # Check agent assignment
        if agent.get("assigned_advertiser_id", "") != advertiser_id:
            if agent.get("assigned_advertiser_id", "") == "":
                return {"success": False, "error": "Agent is not assigned to any advertiser."}
            else:
                return {"success": False, "error": "Agent is assigned to a different advertiser."}

        # Unassign
        self.agents[agent_id]["assigned_advertiser_id"] = ""
        self.agents[agent_id]["availability"] = True
        return {
            "success": True,
            "message": f"Agent {agent_id} unassigned from advertiser {advertiser_id}."
        }

    def update_agent_availability(self, agent_id: str, availability: bool) -> dict:
        """
        Change an agent's availability status.

        Args:
            agent_id (str): The unique identifier for the agent.
            availability (bool): The desired availability status (True for available, False for unavailable).

        Returns:
            dict: 
                On success: { "success": True, "message": "Agent availability updated." }
                On failure: { "success": False, "error": "Agent not found." }

        Constraints:
            - The agent must exist in the system.
        """
        agent = self.agents.get(agent_id)
        if agent is None:
            return { "success": False, "error": "Agent not found." }
    
        agent["availability"] = availability
        return { "success": True, "message": "Agent availability updated." }

    def create_recommendation_for_advertiser(self, advertiser_id: str) -> dict:
        """
        Generate and store a new agent recommendation for a given advertiser based on current matching logic.

        Args:
            advertiser_id (str): The advertiser's unique identifier.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Recommendation created for advertiser <id>" }
                On failure:
                    { "success": False, "error": <reason> }

        Constraints:
            - Advertiser must exist.
            - Only agents with availability=True are considered.
            - Agent's expertise should match the advertiser's industry.
            - Assignment/exclusivity rules are respected (for now: single assignment with assigned_advertiser_id).
        """

        advertiser = self.advertisers.get(advertiser_id)
        if advertiser is None:
            return { "success": False, "error": f"Advertiser '{advertiser_id}' does not exist" }

        # Matching logic: available agents, expertise matches advertiser industry, not assigned elsewhere
        matching_agents = []
        for agent_id, agent in self.agents.items():
            if not agent.get("availability", False):
                continue
            # Basic assignment/exclusivity: must either be unassigned, or assigned to this advertiser
            # If assigned_advertiser_id is "", None, or matches this advertiser, it's OK
            assigned_adv = agent.get("assigned_advertiser_id")
            allowed_assign = (not assigned_adv) or (assigned_adv == advertiser_id)
            if not allowed_assign:
                continue
            # Expertise/industry match
            if (agent.get("expertise", "").lower() == advertiser.get("industry", "").lower()):
                matching_agents.append(agent_id)

        timestamp = str(int(time.time()))
        if matching_agents:
            reasoning = (
                f"Recommended agents based on availability and expertise matching the advertiser's industry: "
                f"{advertiser['industry']}."
            )
        else:
            reasoning = (
                "No available agents matched the advertiser's industry. "
                "Recommendation list is empty."
            )

        rec_info = {
            "advertiser_id": advertiser_id,
            "recommended_agent_ids": matching_agents,
            "timestamp": timestamp,
            "recommendation_reasoning": reasoning,
        }
        self.recommendations[advertiser_id] = rec_info

        return {
            "success": True,
            "message": f"Recommendation created for advertiser {advertiser_id}"
        }

    def update_recommendation_reasoning(
        self,
        advertiser_id: str,
        reasoning: str,
        mode: str = "replace"
    ) -> dict:
        """
        Edit or append reasoning to a recommendation record for a given advertiser.

        Args:
            advertiser_id (str): The advertiser whose recommendation to update.
            reasoning (str): The text to set or append.
            mode (str): "replace" (default: overwrite), "append" (add to existing reasoning).

        Returns:
            dict: {
                "success": True,
                "message": str  # Description of successful update
            }
            or
            {
                "success": False,
                "error": str  # Error description
            }

        Constraints:
            - advertiser_id must exist in recommendations.
            - mode must be "replace" or "append".
            - reasoning must be a non-empty string.
        """
        if advertiser_id not in self.recommendations:
            return {"success": False, "error": "No recommendation found for this advertiser."}
        if not isinstance(reasoning, str) or not reasoning.strip():
            return {"success": False, "error": "Reasoning text must be a non-empty string."}
        if mode not in ("replace", "append"):
            return {"success": False, "error": "Invalid mode. Must be 'replace' or 'append'."}

        rec = self.recommendations[advertiser_id]
        if mode == "replace":
            rec["recommendation_reasoning"] = reasoning
            updated_message = "Recommendation reasoning replaced successfully."
        else:  # mode == "append"
            if rec["recommendation_reasoning"]:
                rec["recommendation_reasoning"] += " " + reasoning
            else:
                rec["recommendation_reasoning"] = reasoning
            updated_message = "Recommendation reasoning appended successfully."
        return {"success": True, "message": updated_message}

    def remove_recommendation_for_advertiser(self, advertiser_id: str) -> dict:
        """
        Delete/remove the current recommendation record for the specified advertiser.

        Args:
            advertiser_id (str): The ID of the advertiser.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Recommendation for advertiser <id> removed." }
                On failure:
                    { "success": False, "error": "<reason>" }

        Constraints:
            - The advertiser_id must exist in self.advertisers.
            - There must be a recommendation present for the advertiser to remove.
        """
        if advertiser_id not in self.advertisers:
            return { "success": False, "error": f"Advertiser ID '{advertiser_id}' does not exist." }

        if advertiser_id not in self.recommendations:
            return { "success": False, "error": "No recommendation found for this advertiser." }

        del self.recommendations[advertiser_id]
        return { "success": True, "message": f"Recommendation for advertiser {advertiser_id} removed." }

    def update_campaign_status(self, campaign_id: str, new_status: str) -> dict:
        """
        Change the status of a campaign (e.g., 'active', 'paused', 'completed').

        Args:
            campaign_id (str): The ID of the campaign to update.
            new_status (str): The new status to assign to the campaign.

        Returns:
            dict: {
                "success": True,
                "message": "Campaign status updated to '<new_status>'."
            }
            or
            {
                "success": False,
                "error": "Campaign not found."
            }

        Constraints:
            - Campaign must exist.
            - Status can be any string (no validation enforced here).
        """
        if campaign_id not in self.campaigns:
            return { "success": False, "error": "Campaign not found." }

        current_status = self.campaigns[campaign_id]['status']
        if current_status == new_status:
            return {
                "success": True,
                "message": f"Campaign status is already '{new_status}'. No update necessary."
            }

        self.campaigns[campaign_id]['status'] = new_status
        return {
            "success": True,
            "message": f"Campaign status updated to '{new_status}'."
        }

    def add_campaign_for_advertiser(
        self,
        campaign_id: str,
        advertiser_id: str,
        objective: str,
        budget: float,
        status: str
    ) -> dict:
        """
        Create and link a new campaign to an advertiser.

        Args:
            campaign_id (str): Unique ID for the new campaign.
            advertiser_id (str): ID of the advertiser to link the campaign to.
            objective (str): The objective/goal of the campaign.
            budget (float): The budget allocated for the campaign. Must be non-negative.
            status (str): The current status of the campaign.

        Returns:
            dict: {
                "success": True,
                "message": "Campaign <id> added for advertiser <id>"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - campaign_id must be unique.
            - advertiser_id must exist.
            - budget must be non-negative.
            - status/objective must be non-empty strings.
        """
        if not campaign_id or not isinstance(campaign_id, str):
            return {"success": False, "error": "Invalid or missing campaign_id."}
        if campaign_id in self.campaigns:
            return {"success": False, "error": "Campaign ID already exists."}

        if advertiser_id not in self.advertisers:
            return {"success": False, "error": "Advertiser ID does not exist."}

        if not isinstance(budget, (int, float)) or budget < 0:
            return {"success": False, "error": "Budget must be a non-negative number."}

        if not isinstance(objective, str) or not objective.strip():
            return {"success": False, "error": "Objective must be a non-empty string."}
        if not isinstance(status, str) or not status.strip():
            return {"success": False, "error": "Status must be a non-empty string."}

        new_campaign = {
            "campaign_id": campaign_id,
            "advertiser_id": advertiser_id,
            "objective": objective,
            "budget": float(budget),
            "status": status
        }
        self.campaigns[campaign_id] = new_campaign

        return {
            "success": True,
            "message": f"Campaign {campaign_id} added for advertiser {advertiser_id}"
        }


class DigitalAdvertisingManagementPlatform(BaseEnv):
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

    def get_advertiser_by_id(self, **kwargs):
        return self._call_inner_tool('get_advertiser_by_id', kwargs)

    def list_advertisers(self, **kwargs):
        return self._call_inner_tool('list_advertisers', kwargs)

    def get_agent_by_id(self, **kwargs):
        return self._call_inner_tool('get_agent_by_id', kwargs)

    def list_agents(self, **kwargs):
        return self._call_inner_tool('list_agents', kwargs)

    def get_agents_by_expertise(self, **kwargs):
        return self._call_inner_tool('get_agents_by_expertise', kwargs)

    def get_available_agents(self, **kwargs):
        return self._call_inner_tool('get_available_agents', kwargs)

    def get_assigned_agents_for_advertiser(self, **kwargs):
        return self._call_inner_tool('get_assigned_agents_for_advertiser', kwargs)

    def get_advertiser_campaigns(self, **kwargs):
        return self._call_inner_tool('get_advertiser_campaigns', kwargs)

    def get_campaign_by_id(self, **kwargs):
        return self._call_inner_tool('get_campaign_by_id', kwargs)

    def get_recommendation_by_advertiser(self, **kwargs):
        return self._call_inner_tool('get_recommendation_by_advertiser', kwargs)

    def get_recommendation_history(self, **kwargs):
        return self._call_inner_tool('get_recommendation_history', kwargs)

    def check_agent_availability(self, **kwargs):
        return self._call_inner_tool('check_agent_availability', kwargs)

    def check_agent_assignment_limit(self, **kwargs):
        return self._call_inner_tool('check_agent_assignment_limit', kwargs)

    def check_advertiser_agent_exclusivity(self, **kwargs):
        return self._call_inner_tool('check_advertiser_agent_exclusivity', kwargs)

    def match_agents_for_advertiser(self, **kwargs):
        return self._call_inner_tool('match_agents_for_advertiser', kwargs)

    def assign_agent_to_advertiser(self, **kwargs):
        return self._call_inner_tool('assign_agent_to_advertiser', kwargs)

    def unassign_agent_from_advertiser(self, **kwargs):
        return self._call_inner_tool('unassign_agent_from_advertiser', kwargs)

    def update_agent_availability(self, **kwargs):
        return self._call_inner_tool('update_agent_availability', kwargs)

    def create_recommendation_for_advertiser(self, **kwargs):
        return self._call_inner_tool('create_recommendation_for_advertiser', kwargs)

    def update_recommendation_reasoning(self, **kwargs):
        return self._call_inner_tool('update_recommendation_reasoning', kwargs)

    def remove_recommendation_for_advertiser(self, **kwargs):
        return self._call_inner_tool('remove_recommendation_for_advertiser', kwargs)

    def update_campaign_status(self, **kwargs):
        return self._call_inner_tool('update_campaign_status', kwargs)

    def add_campaign_for_advertiser(self, **kwargs):
        return self._call_inner_tool('add_campaign_for_advertiser', kwargs)
