# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



class ChampionInfo(TypedDict):
    champion_id: str
    name: str
    role: str
    release_date: str
    base_stat: float  # Could be a dict if stats are structured, but using float as per "base_sta"

class AbilityInfo(TypedDict):
    ability_id: str
    champion_id: str
    name: str
    description: str
    cooldown: float
    damage: float

class PerformanceMetricInfo(TypedDict):
    champion_id: str
    rank: str
    win_rate: float
    pick_rate: float
    ban_rate: float
    average_kda: float

class RankInfo(TypedDict):
    rank_id: str
    name: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for managing game champion metadata, abilities, ranks, and performance metrics.
        """

        # Champions: {champion_id: ChampionInfo}
        # Represents each individual champion, storing name, role, etc.
        self.champions: Dict[str, ChampionInfo] = {}

        # Abilities: {ability_id: AbilityInfo}
        # Each ability belongs to a champion and details damage, cooldown, etc.
        self.abilities: Dict[str, AbilityInfo] = {}

        # Performance Metrics: List of {champion_id, rank, ...}
        # Each metric links a champion and a rank to various stats.
        self.performance_metrics: List[PerformanceMetricInfo] = []

        # Ranks: {rank_id: RankInfo}
        # List of available ranks, e.g., grandmaster, challenger, etc.
        self.ranks: Dict[str, RankInfo] = {}

        # Constraint Rules:
        # - Each performance metric must reference both a champion and a rank.
        # - Each ability must reference a valid champion.
        # - Each champion must have at least one associated ability.
        # - Rank values must be from a predefined set (e.g., grandmaster, challenger, etc.).

    def get_champion_by_name(self, name: str) -> dict:
        """
        Retrieve metadata for a champion given their name.

        Args:
            name (str): The name of the champion to query.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": ChampionInfo
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Champion not found"
                    }

        Constraints:
            - The name must match an existing champion entry.
        """
        for champion in self.champions.values():
            if champion["name"] == name:
                return { "success": True, "data": champion }
        return { "success": False, "error": "Champion not found" }

    def list_all_champions(self) -> dict:
        """
        Retrieve metadata for all champions in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[ChampionInfo]  # May be empty if there are no champions
            }
            or
            {
                "success": False,
                "error": str  # Description of any error (should not occur in normal operation)
            }

        Constraints:
            - None for this query; returns all ChampionInfo objects currently in the system.
        """
        if not hasattr(self, "champions") or self.champions is None:
            return {"success": False, "error": "Champion records unavailable"}
        return {"success": True, "data": list(self.champions.values())}

    def list_all_champion_names(self) -> dict:
        """
        Retrieve the names of all available champions.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[str],  # List of all champion names (possibly empty)
            }
        """
        names = [champion_info["name"] for champion_info in self.champions.values()]
        return { "success": True, "data": names }

    def get_champion_abilities(self, champion_id: str) -> dict:
        """
        List all abilities associated with a given champion.

        Args:
            champion_id (str): The unique identifier of the champion.

        Returns:
            dict:
                - { "success": True, "data": List[AbilityInfo] }
                  If the champion exists, returns a list (possibly empty) of AbilityInfo dicts.
                - { "success": False, "error": str }
                  If the champion_id does not exist in the database.
        Constraints:
            - The champion_id must exist in self.champions.
            - Each ability is associated by its 'champion_id' field.
        """
        if champion_id not in self.champions:
            return { "success": False, "error": "Champion not found" }
    
        abilities = [
            ability_info for ability_info in self.abilities.values()
            if ability_info['champion_id'] == champion_id
        ]

        return { "success": True, "data": abilities }

    def get_champion_performance_metrics_by_rank(
        self, champion_id: str, ranks: list
    ) -> dict:
        """
        Retrieve the performance metrics for a specific champion, filtered by one or more ranks.

        Args:
            champion_id (str): The ID of the champion to retrieve metrics for.
            ranks (List[str]): A list of rank names (e.g., ["grandmaster", "challenger"]) to filter metrics by.

        Returns:
            dict: {
                "success": True,
                "data": [PerformanceMetricInfo, ...]  # Metrics for the given champion and ranks (may be empty)
            }
            OR
            {
                "success": False,
                "error": str  # Reason for failure: champion not found or invalid ranks
            }

        Constraints:
            - champion_id must exist in self.champions
            - All entries in ranks must match an existing RankInfo.name in self.ranks
            - No error if metrics are missing for some/all ranks; simply return those that exist
        """
        # Validate Champion
        if champion_id not in self.champions:
            return {"success": False, "error": "Champion not found"}

        # Valid rank names
        valid_rank_names = {rank_info["name"] for rank_info in self.ranks.values()}
        invalid_ranks = [r for r in ranks if r not in valid_rank_names]
        if invalid_ranks:
            return {"success": False, "error": f"Invalid rank(s): {', '.join(invalid_ranks)}"}

        # Do filtering
        metrics = [
            metric for metric in self.performance_metrics
            if metric["champion_id"] == champion_id and metric["rank"] in ranks
        ]
        return {"success": True, "data": metrics}

    def list_all_ranks(self) -> dict:
        """
        Return a list of all available player ranks.

        Returns:
            dict: {
                'success': True,
                'data': List[RankInfo],  # Each entry has rank_id and name; list may be empty
            }
        """
        all_ranks = list(self.ranks.values())
        return {
            "success": True,
            "data": all_ranks
        }

    def get_performance_metrics_for_champion(self, champion_id: str) -> dict:
        """
        Return all performance metrics associated with a specific champion across all available ranks.

        Args:
            champion_id (str): The ID of the champion to fetch metrics for.

        Returns:
            dict: {
                "success": True,
                "data": List[PerformanceMetricInfo],  # All metrics for this champion (possibly empty)
            }
            or
            {
                "success": False,
                "error": str  # If champion ID is invalid/not present
            }

        Constraints:
            - The champion_id must exist in the system.
        """
        if champion_id not in self.champions:
            return { "success": False, "error": "Champion does not exist" }

        metrics = [
            metric for metric in self.performance_metrics
            if metric["champion_id"] == champion_id
        ]

        return { "success": True, "data": metrics }

    def get_performance_metrics_for_rank(self, rank: str) -> dict:
        """
        Return all performance metrics for all champions at the given rank.

        Args:
            rank (str): The name of the rank to retrieve metrics for (e.g., 'grandmaster').

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[PerformanceMetricInfo],  # List may be empty
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason for failure, e.g., rank does not exist
                    }

        Constraints:
            - Provided rank name must exist in the ranks list.
        """
        # Check if rank exists in self.ranks (by name)
        rank_exists = any(rank_info["name"] == rank for rank_info in self.ranks.values())
        if not rank_exists:
            return { "success": False, "error": f"Rank '{rank}' does not exist" }

        relevant_metrics = [
            metric for metric in self.performance_metrics
            if metric["rank"] == rank
        ]

        return { "success": True, "data": relevant_metrics }

    def get_ability_by_id(self, ability_id: str) -> dict:
        """
        Retrieve detailed information about an ability given its ability_id.

        Args:
            ability_id (str): The unique identifier of the ability.

        Returns:
            dict: {
                "success": True,
                "data": AbilityInfo  # All metadata for the ability
            }
            OR
            {
                "success": False,
                "error": str  # "Ability not found"
            }

        Constraints:
            - The ability_id must exist in the ability registry.
        """
        ability = self.abilities.get(ability_id)
        if ability is None:
            return { "success": False, "error": "Ability not found" }
        return { "success": True, "data": ability }

    def add_champion(
        self, 
        champion_id: str, 
        name: str, 
        role: str, 
        release_date: str, 
        base_stat: float
    ) -> dict:
        """
        Add a new champion to the system with required metadata.

        Args:
            champion_id (str): Unique identifier for the champion.
            name (str): Champion name.
            role (str): Champion role (e.g., mage, tank, etc.).
            release_date (str): Release date of the champion (any string format).
            base_stat (float): Base stat value (float).

        Returns:
            dict: {
                "success": True,
                "message": "Champion <name> (<champion_id>) added successfully."
            }
            or
            {
                "success": False,
                "error": "Reason for failure."
            }

        Constraints:
            - Champion ID must be unique in the system.
            - All fields must be non-empty/valid.
            - Does not create abilities (abilities must be added separately).
        """
        # Validate parameters
        if not all([champion_id, name, role, release_date]) or not isinstance(base_stat, (int, float)):
            return { "success": False, "error": "Missing or invalid champion metadata." }
        if champion_id in self.champions:
            return { "success": False, "error": "Champion ID already exists." }

        champion_info: ChampionInfo = {
            "champion_id": champion_id,
            "name": name,
            "role": role,
            "release_date": release_date,
            "base_stat": float(base_stat),
        }
        self.champions[champion_id] = champion_info
        return {
            "success": True,
            "message": f"Champion {name} ({champion_id}) added successfully."
        }

    def update_champion_metadata(
        self,
        champion_id: str,
        name: str = None,
        role: str = None,
        release_date: str = None,
        base_stat: float = None
    ) -> dict:
        """
        Update an existing champion's metadata (name, role, release_date, base_stat).

        Args:
            champion_id (str): ID of the champion to update.
            name (str, optional): New name (if updating).
            role (str, optional): New role (if updating).
            release_date (str, optional): New release date (if updating).
            base_stat (float, optional): New base statistic (if updating).

        Returns:
            dict:
                Success: { "success": True, "message": "Champion metadata updated" }
                Failure: { "success": False, "error": "reason" }

        Constraints:
            - champion_id must exist in self.champions.
            - At least one field should be provided for update.
            - Types should match (no deep validation).
        """
        if champion_id not in self.champions:
            return { "success": False, "error": "Champion not found" }

        # Check at least one value to update is provided
        if all(param is None for param in [name, role, release_date, base_stat]):
            return { "success": False, "error": "No update parameters provided" }

        # Proceed to update values if provided
        champion = self.champions[champion_id]
        updated = False
        if name is not None:
            champion["name"] = name
            updated = True
        if role is not None:
            champion["role"] = role
            updated = True
        if release_date is not None:
            champion["release_date"] = release_date
            updated = True
        if base_stat is not None:
            champion["base_stat"] = base_stat
            updated = True

        # Save the update back (since dict is mutable, this is for completeness)
        self.champions[champion_id] = champion

        return { "success": True, "message": "Champion metadata updated" }

    def delete_champion(self, champion_id: str) -> dict:
        """
        Remove a champion and all associated abilities and performance metrics.

        Args:
            champion_id (str): The identifier of the champion to delete.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "message": "Champion <champion_name> and all associations deleted"
                    }
                On failure:
                    {
                        "success": False,
                        "error": "<reason>"
                    }

        Constraints:
            - All abilities and performance metrics linked to the champion will be deleted.
            - If the champion_id does not exist, operation fails.
            - No abilities or metrics referencing the champion may remain after deletion.
        """
        # Check if champion exists
        champ = self.champions.get(champion_id)
        if champ is None:
            return { "success": False, "error": "Champion does not exist" }

        # Remove all abilities that reference this champion
        abilities_to_remove = [ability_id for ability_id, ability in self.abilities.items()
                               if ability["champion_id"] == champion_id]
        for ability_id in abilities_to_remove:
            del self.abilities[ability_id]

        # Remove all performance metrics for this champion
        before_metrics = len(self.performance_metrics)
        self.performance_metrics = [
            metric for metric in self.performance_metrics
            if metric["champion_id"] != champion_id
        ]
        after_metrics = len(self.performance_metrics)
        deleted_metrics_count = before_metrics - after_metrics

        # Delete the champion from champions dict
        champion_name = champ.get("name", champion_id)
        del self.champions[champion_id]

        return {
            "success": True,
            "message": f"Champion '{champion_name}' and all associated abilities and {deleted_metrics_count} performance metrics deleted"
        }

    def add_ability_to_champion(
        self,
        ability_id: str,
        champion_id: str,
        name: str,
        description: str,
        cooldown: float,
        damage: float
    ) -> dict:
        """
        Add a new ability to a champion.

        Args:
            ability_id (str): Unique ID for the new ability.
            champion_id (str): The ID of the champion to attach the ability to; must exist.
            name (str): Name of the new ability.
            description (str): Description of the new ability.
            cooldown (float): Cooldown time of the ability.
            damage (float): Damage value of the ability.

        Returns:
            dict: {
                "success": True,
                "message": "Ability added to champion <champion_id>"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Champion must exist.
            - ability_id must be unique.
        """
        # Check for existence of champion
        if champion_id not in self.champions:
            return {"success": False, "error": "Champion does not exist"}

        # Check ability_id uniqueness
        if ability_id in self.abilities:
            return {"success": False, "error": "Ability ID already exists"}

        # Basic parameter checks (naive type-checking, can be expanded)
        if not ability_id or not isinstance(ability_id, str):
            return {"success": False, "error": "Missing or invalid parameter: ability_id"}
        if not name or not isinstance(name, str):
            return {"success": False, "error": "Missing or invalid parameter: name"}
        if not description or not isinstance(description, str):
            return {"success": False, "error": "Missing or invalid parameter: description"}
        try:
            cd = float(cooldown)
            dmg = float(damage)
        except (TypeError, ValueError):
            return {"success": False, "error": "Missing or invalid parameter: cooldown/damage"}

        # Construct and store the new ability
        new_ability = {
            "ability_id": ability_id,
            "champion_id": champion_id,
            "name": name,
            "description": description,
            "cooldown": cd,
            "damage": dmg
        }
        self.abilities[ability_id] = new_ability

        return {
            "success": True,
            "message": f"Ability added to champion {champion_id}"
        }

    def update_ability(
        self, 
        ability_id: str, 
        name: str = None, 
        description: str = None,
        cooldown: float = None, 
        damage: float = None, 
        champion_id: str = None
    ) -> dict:
        """
        Update properties of an existing ability.

        Args:
            ability_id (str): The ID of the ability to update.
            name (str, optional): New ability name.
            description (str, optional): New description.
            cooldown (float, optional): New cooldown.
            damage (float, optional): New damage value.
            champion_id (str, optional): New champion_id to assign this ability.

        Returns:
            dict: {
                "success": True,
                "message": "Ability <ability_id> updated successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }
    
        Constraints:
            - ability_id must exist.
            - If champion_id is updated, it must refer to an existing champion.
            - Properties should be updated only if new values are provided.
            - Types should be respected if given (cooldown, damage as float).
        """
        # Check if ability exists
        if ability_id not in self.abilities:
            return {"success": False, "error": "Ability ID does not exist."}

        ability = self.abilities[ability_id]

        # If changing champion_id, validate existence
        if champion_id is not None and champion_id != ability["champion_id"]:
            if champion_id not in self.champions:
                return {"success": False, "error": "New champion_id does not exist."}
            ability["champion_id"] = champion_id

        if name is not None:
            ability["name"] = name
        if description is not None:
            ability["description"] = description
        if cooldown is not None:
            # Type checking (optional)
            try:
                ability["cooldown"] = float(cooldown)
            except (ValueError, TypeError):
                return {"success": False, "error": "cooldown must be a float."}
        if damage is not None:
            try:
                ability["damage"] = float(damage)
            except (ValueError, TypeError):
                return {"success": False, "error": "damage must be a float."}

        self.abilities[ability_id] = ability

        return {"success": True, "message": f"Ability {ability_id} updated successfully."}

    def remove_ability(self, ability_id: str) -> dict:
        """
        Remove an ability from a champion.

        Args:
            ability_id (str): The unique ID of the ability to be removed.

        Returns:
            dict:
                - success: True and a message if removal is successful.
                - success: False and an error message if:
                    - The ability does not exist.
                    - Removing it would leave the champion with no abilities (forbidden).
                    - Referenced champion does not exist.

        Constraints:
            - Each champion must have at least one associated ability after removal.
        """
        if ability_id not in self.abilities:
            return { "success": False, "error": f"Ability '{ability_id}' does not exist." }

        ability_info = self.abilities[ability_id]
        champion_id = ability_info["champion_id"]

        if champion_id not in self.champions:
            return { "success": False, "error": f"Champion '{champion_id}' referenced by ability does not exist." }

        # Count current abilities for this champion
        champ_abilities = [
            a for a in self.abilities.values() if a["champion_id"] == champion_id
        ]

        if len(champ_abilities) <= 1:
            return {
                "success": False,
                "error": f"Cannot remove ability '{ability_id}': champion '{champion_id}' must have at least one ability."
            }

        # All checks passed - remove
        del self.abilities[ability_id]
        return {
            "success": True,
            "message": f"Ability '{ability_id}' removed from champion '{champion_id}'."
        }

    def add_performance_metric(
        self,
        champion_id: str,
        rank: str,
        win_rate: float,
        pick_rate: float,
        ban_rate: float,
        average_kda: float
    ) -> dict:
        """
        Adds a new performance metric for a champion at a given rank.

        Args:
            champion_id (str): ID for the champion.
            rank (str): Name of the rank (e.g., 'grandmaster').
            win_rate (float): Win rate at this rank.
            pick_rate (float): Pick rate at this rank.
            ban_rate (float): Ban rate at this rank.
            average_kda (float): Average KDA at this rank.

        Returns:
            dict: 
              - { "success": True, "message": ... } on success
              - { "success": False, "error": ... } if constraints are violated

        Constraints:
            - champion_id must exist in self.champions
            - rank must match one of the RankInfo["name"] in self.ranks
            - Only one metric per (champion_id, rank) is allowed
        """
        # Check champion
        if champion_id not in self.champions:
            return { "success": False, "error": "Champion does not exist." }

        # Check rank (by name)
        valid_ranks = {rank_info["name"] for rank_info in self.ranks.values()}
        if rank not in valid_ranks:
            return { "success": False, "error": "Rank does not exist." }

        # Check uniqueness
        for metric in self.performance_metrics:
            if metric["champion_id"] == champion_id and metric["rank"] == rank:
                return { 
                    "success": False, 
                    "error": "A performance metric for this champion and rank already exists." 
                }

        # Add the performance metric
        new_metric = {
            "champion_id": champion_id,
            "rank": rank,
            "win_rate": win_rate,
            "pick_rate": pick_rate,
            "ban_rate": ban_rate,
            "average_kda": average_kda
        }
        self.performance_metrics.append(new_metric)
        return { 
            "success": True, 
            "message": f"Performance metric added for champion {champion_id} at rank {rank}." 
        }

    def update_performance_metric(
        self,
        champion_id: str,
        rank: str,
        win_rate: float = None,
        pick_rate: float = None,
        ban_rate: float = None,
        average_kda: float = None
    ) -> dict:
        """
        Update a performance metric entry for a specific champion and rank.
    
        Args:
            champion_id (str): The champion's unique identifier.
            rank (str): The rank for the metric (must be a valid rank name).
            win_rate (float, optional): New win rate value.
            pick_rate (float, optional): New pick rate value.
            ban_rate (float, optional): New ban rate value.
            average_kda (float, optional): New average KDA value.
        
        Returns:
            dict: {
                "success": True,
                "message": "Performance metric updated successfully."
            }
            or
            {
                "success": False,
                "error": str
            }
    
        Constraints:
            - The performance metric (champion_id, rank) must exist.
            - Rank must be a valid rank in the system.
            - At least one field to update must be provided.
        """
        # Check rank validity
        if rank not in [rinfo["name"] for rinfo in self.ranks.values()]:
            return { "success": False, "error": f"Rank '{rank}' is not a valid rank." }
    
        # Find the metric
        metric = None
        for m in self.performance_metrics:
            if m["champion_id"] == champion_id and m["rank"] == rank:
                metric = m
                break

        if not metric:
            return { "success": False, "error": "Performance metric not found." }

        fields_to_update = {}
        if win_rate is not None:
            fields_to_update["win_rate"] = win_rate
        if pick_rate is not None:
            fields_to_update["pick_rate"] = pick_rate
        if ban_rate is not None:
            fields_to_update["ban_rate"] = ban_rate
        if average_kda is not None:
            fields_to_update["average_kda"] = average_kda

        if not fields_to_update:
            return { "success": False, "error": "No fields specified for update." }

        for field, value in fields_to_update.items():
            metric[field] = value

        return { "success": True, "message": "Performance metric updated successfully." }

    def delete_performance_metric(self, champion_id: str, rank: str) -> dict:
        """
        Remove a performance metric associated with a given champion and rank.

        Args:
            champion_id (str): The ID of the champion.
            rank (str): The player rank name (e.g., 'grandmaster', 'challenger').

        Returns:
            dict: 
                - On success: { "success": True, "message": "Performance metric for champion <champion_id> at rank <rank> deleted." }
                - On failure: { "success": False, "error": "Performance metric for specified champion and rank does not exist." }

        Constraints:
            - Must delete a metric only if it exists for the given champion and rank.
            - No exception raised: return error dict instead.
        """
        found = False
        new_metrics = []
        for metric in self.performance_metrics:
            if metric["champion_id"] == champion_id and metric["rank"] == rank:
                found = True
                continue  # skip to remove
            new_metrics.append(metric)
        if not found:
            return {
                "success": False,
                "error": f"Performance metric for champion '{champion_id}' at rank '{rank}' does not exist."
            }
        self.performance_metrics = new_metrics
        return {
            "success": True,
            "message": f"Performance metric for champion '{champion_id}' at rank '{rank}' deleted."
        }

    def add_rank(self, rank_id: str, name: str) -> dict:
        """
        Add a new rank to the system from a predefined set of allowed rank names.

        Args:
            rank_id (str): Unique identifier for the rank.
            name (str): The name of the rank (e.g., 'grandmaster', 'challenger').

        Returns:
            dict: {
                "success": True,
                "message": "Rank added successfully"
            }
            or
            {
                "success": False,
                "error": str  # Explanation of failure
            }

        Constraints:
            - `rank_id` must be unique (not already present in self.ranks).
            - `name` must be from the predefined set of allowed rank names.
        """
        ALLOWED_RANK_NAMES = {
            'iron', 'bronze', 'silver', 'gold', 'platinum', 'diamond', 'master', 'grandmaster', 'challenger'
        }

        if not rank_id or not isinstance(rank_id, str):
            return { "success": False, "error": "Invalid or missing rank_id" }
        if not name or not isinstance(name, str):
            return { "success": False, "error": "Invalid or missing rank name" }
        if rank_id in self.ranks:
            return { "success": False, "error": "Rank already exists" }
        if name.lower() not in ALLOWED_RANK_NAMES:
            return { "success": False, "error": "Rank name is not in predefined allowed set" }

        self.ranks[rank_id] = {
            "rank_id": rank_id,
            "name": name
        }

        return { "success": True, "message": "Rank added successfully" }

    def update_rank(self, rank_id: str, name: str = None) -> dict:
        """
        Edit properties (display name) of a rank.

        Args:
            rank_id (str): The unique identifier of the rank to update.
            name (Optional[str]): The new display name of the rank (if changing name).

        Returns:
            dict:
                On success:
                    {"success": True, "message": "Rank updated successfully"}
                On failure:
                    {"success": False, "error": <reason>}

        Constraints:
            - rank_id must exist in the system.
            - Only provided properties (currently: name) are changed.
            - rank_id itself cannot be changed.
        """
        # Check existence
        if rank_id not in self.ranks:
            return {"success": False, "error": "Rank does not exist"}

        updated = False
        if name is not None:
            self.ranks[rank_id]["name"] = name
            updated = True

        if updated:
            return {"success": True, "message": "Rank updated successfully"}
        else:
            return {"success": False, "error": "No properties to update"}

    def delete_rank(self, rank_id: str) -> dict:
        """
        Remove a rank from the system if no performance metrics reference it.

        Args:
            rank_id (str): The unique identifier of the rank to delete.

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
            - Cannot delete the rank if any performance metric references it.
            - Rank must exist.
        """
        if rank_id not in self.ranks:
            return { "success": False, "error": f"Rank with id '{rank_id}' does not exist." }
        rank_name = self.ranks[rank_id]["name"]

        for metric in self.performance_metrics:
            if metric["rank"] == rank_name:
                return {
                    "success": False,
                    "error": f"Cannot delete rank '{rank_name}' because it is still referenced by at least one performance metric."
                }

        del self.ranks[rank_id]
        return {
            "success": True,
            "message": f"Rank '{rank_name}' deleted successfully."
        }


class ChampionMetadataManagementSystem(BaseEnv):
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

    def get_champion_by_name(self, **kwargs):
        return self._call_inner_tool('get_champion_by_name', kwargs)

    def list_all_champions(self, **kwargs):
        return self._call_inner_tool('list_all_champions', kwargs)

    def list_all_champion_names(self, **kwargs):
        return self._call_inner_tool('list_all_champion_names', kwargs)

    def get_champion_abilities(self, **kwargs):
        return self._call_inner_tool('get_champion_abilities', kwargs)

    def get_champion_performance_metrics_by_rank(self, **kwargs):
        return self._call_inner_tool('get_champion_performance_metrics_by_rank', kwargs)

    def list_all_ranks(self, **kwargs):
        return self._call_inner_tool('list_all_ranks', kwargs)

    def get_performance_metrics_for_champion(self, **kwargs):
        return self._call_inner_tool('get_performance_metrics_for_champion', kwargs)

    def get_performance_metrics_for_rank(self, **kwargs):
        return self._call_inner_tool('get_performance_metrics_for_rank', kwargs)

    def get_ability_by_id(self, **kwargs):
        return self._call_inner_tool('get_ability_by_id', kwargs)

    def add_champion(self, **kwargs):
        return self._call_inner_tool('add_champion', kwargs)

    def update_champion_metadata(self, **kwargs):
        return self._call_inner_tool('update_champion_metadata', kwargs)

    def delete_champion(self, **kwargs):
        return self._call_inner_tool('delete_champion', kwargs)

    def add_ability_to_champion(self, **kwargs):
        return self._call_inner_tool('add_ability_to_champion', kwargs)

    def update_ability(self, **kwargs):
        return self._call_inner_tool('update_ability', kwargs)

    def remove_ability(self, **kwargs):
        return self._call_inner_tool('remove_ability', kwargs)

    def add_performance_metric(self, **kwargs):
        return self._call_inner_tool('add_performance_metric', kwargs)

    def update_performance_metric(self, **kwargs):
        return self._call_inner_tool('update_performance_metric', kwargs)

    def delete_performance_metric(self, **kwargs):
        return self._call_inner_tool('delete_performance_metric', kwargs)

    def add_rank(self, **kwargs):
        return self._call_inner_tool('add_rank', kwargs)

    def update_rank(self, **kwargs):
        return self._call_inner_tool('update_rank', kwargs)

    def delete_rank(self, **kwargs):
        return self._call_inner_tool('delete_rank', kwargs)

