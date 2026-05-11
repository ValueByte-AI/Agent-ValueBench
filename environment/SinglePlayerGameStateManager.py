# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict
from pathlib import Path
import re

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Any
import json
from typing import Dict



class PlayerCharacterInfo(TypedDict):
    character_id: str
    name: str
    level: int
    experience_points: int
    health: int
    mana: int
    stats: Dict[str, int]           # e.g., {'strength': 10, 'agility': 8}
    position: Dict[str, Any]        # e.g., {'x': 10, 'y': 5, 'zone': 'town'}, or tuple
    skills: List[str]
    current_status_effects: List[str]

class InventoryItemInfo(TypedDict):
    item_id: str
    name: str
    quantity: int
    attributes: Dict[str, Any]      # e.g., {'damage': 10, 'durability': 80}

class InventoryInfo(TypedDict):
    inventory_id: str
    character_id: str
    item_list: List[InventoryItemInfo]

class GameWorldInfo(TypedDict):
    world_state_id: str
    visited_locations: List[str]
    unlocked_areas: List[str]
    world_variables: Dict[str, Any]    # e.g., {'weather': 'rainy', 'time_of_day': 'night'}
    npc_states: Dict[str, Any]         # e.g., {'npc_42': 'friendly'}

class MilestoneInfo(TypedDict):
    milestone_id: str
    description: str
    status: str           # 'completed', 'in_progress', etc.
    timestamp: str

class _GeneratedEnvImpl:
    def __init__(self):
        # PlayerCharacters: {character_id: PlayerCharacterInfo}
        self.characters: Dict[str, PlayerCharacterInfo] = {}
        # Inventories: {inventory_id: InventoryInfo}
        self.inventories: Dict[str, InventoryInfo] = {}
        # InventoryItems: {item_id: InventoryItemInfo}
        self.items: Dict[str, InventoryItemInfo] = {}
        # GameWorlds: {world_state_id: GameWorldInfo}
        self.game_worlds: Dict[str, GameWorldInfo] = {}
        # Milestones: {milestone_id: MilestoneInfo}
        self.milestones: Dict[str, MilestoneInfo] = {}

        # Constraints:
        # - PlayerCharacter’s health and stats must remain within defined min/max limits.
        # - Player inventory cannot exceed a specified size or weight limit.
        # - Only milestones relevant to the player’s game version and progress can be in in-progress states.
        # - GameWorld state must be updated to reflect persistent changes from player actions or story events.
        # - Relationships (e.g., player-inventory, world-milestones) must be maintained for accurate serialization and deserialization.
        self._virtual_saved_paths: Dict[str, str] = {}

    def _repo_root(self) -> Path:
        return Path(__file__).resolve().parent.parent

    def _resolve_world_key(self, world_ref: str):
        if world_ref in self.game_worlds:
            return world_ref
        for key, world in self.game_worlds.items():
            if world.get("world_state_id") == world_ref:
                return key
        return None

    def _resolve_load_path(self, json_file_path: str):
        requested = Path(json_file_path)
        if requested.exists():
            return requested

        mapped = self._virtual_saved_paths.get(json_file_path)
        if mapped and Path(mapped).exists():
            return Path(mapped)

        repo_root = self._repo_root()
        candidates = []
        if requested.is_absolute():
            candidates.append(repo_root / requested.name)
        else:
            candidates.append(Path.cwd() / requested)
            candidates.append(repo_root / requested)
            candidates.append(repo_root / requested.name)

        seen = set()
        for candidate in candidates:
            candidate = candidate.resolve()
            if str(candidate) in seen:
                continue
            seen.add(str(candidate))
            if candidate.exists():
                return candidate
        return None

    def _resolve_save_path(self, file_path: str) -> Path:
        requested = Path(file_path)
        if not requested.is_absolute():
            actual = (Path.cwd() / requested).resolve()
            self._virtual_saved_paths[file_path] = str(actual)
            return actual

        repo_root = self._repo_root()
        safe_dir = repo_root / ".single_player_game_state_saves"
        safe_dir.mkdir(parents=True, exist_ok=True)
        sanitized = re.sub(r"[^A-Za-z0-9_.-]+", "_", file_path.lstrip("/"))
        actual = (safe_dir / sanitized).resolve()
        self._virtual_saved_paths[file_path] = str(actual)
        return actual

    def get_player_character(self, character_id: str) -> dict:
        """
        Retrieve the complete player character information by character_id.

        Args:
            character_id (str): Unique identifier for the player character.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": PlayerCharacterInfo  # player character information
                }
                OR
                {
                    "success": False,
                    "error": str  # error message, e.g., character not found
                }
        Constraints:
            - character_id must exist in self.characters.
        """
        if character_id not in self.characters:
            return {"success": False, "error": "Player character not found"}
        return {"success": True, "data": self.characters[character_id]}

    def get_player_inventory(self, character_id: str) -> dict:
        """
        Retrieve the inventory associated with a player character.

        Args:
            character_id (str): The unique identifier for the player character.

        Returns:
            dict: {
                "success": True,
                "data": InventoryInfo  # The inventory info for the character
            }
            or
            {
                "success": False,
                "error": str  # Error message, e.g. player does not exist, or no inventory
            }

        Constraints:
            - character_id must correspond to an existing player character.
            - The player must have an inventory associated (via character_id).
        """
        if character_id not in self.characters:
            return { "success": False, "error": "Player character does not exist" }

        for inventory in self.inventories.values():
            if inventory["character_id"] == character_id:
                return { "success": True, "data": inventory }

        return { "success": False, "error": "No inventory found for player" }

    def get_inventory_items(self, inventory_id: str) -> dict:
        """
        List all items with their full properties in a specified inventory.

        Args:
            inventory_id (str): The ID of the inventory to query.

        Returns:
            dict: {
                "success": True,
                "data": List[InventoryItemInfo],  # All item info in the inventory (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # e.g., "Inventory not found"
            }

        Constraints:
            - The inventory with the given ID must exist.

        Edge cases:
            - Returns an empty list if the inventory contains no items.
        """
        inventory = self.inventories.get(inventory_id)
        if inventory is None:
            return { "success": False, "error": "Inventory not found" }

        items = inventory.get("item_list", [])
        return { "success": True, "data": items }

    def get_game_world_state(self) -> dict:
        """
        Retrieve the current game world state information.

        Returns:
            dict:
                - success: True and data set to GameWorldInfo dict if found.
                - success: False and error message if no game world state exists.

        Notes:
            - If there are multiple game worlds tracked, returns the first one found.
            - If no worlds exist, returns an error.
            - This operation does not check or enforce any constraints; it returns the raw game world state.
        """
        if not self.game_worlds:
            return { "success": False, "error": "No game world state found" }

        # If multiple worlds, select the first one arbitrarily.
        first_world = next(iter(self.game_worlds.values()))
        return { "success": True, "data": first_world }

    def get_player_milestones(self) -> dict:
        """
        Retrieve all milestones relevant to the current player, including their progress statuses.

        Returns:
            dict: {
                "success": True,
                "data": List[MilestoneInfo]  # May be empty if no milestones exist
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., no player character)
            }

        Constraints:
            - If there are no player characters, the method fails.
            - If milestones are present, all are assumed relevant (as no specific mapping available).
        """
        if not self.characters:
            return {"success": False, "error": "No player character found."}

        # Optionally, more advanced logic for matching milestones to player
        milestones_list = list(self.milestones.values())

        return {"success": True, "data": milestones_list}

    def get_full_game_state(self) -> dict:
        """
        Retrieve the entire, current game state for serialization,
        including all player characters, inventories, items, world states, and milestones.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "characters": Dict[str, PlayerCharacterInfo],
                    "inventories": Dict[str, InventoryInfo],
                    "items": Dict[str, InventoryItemInfo],
                    "game_worlds": Dict[str, GameWorldInfo],
                    "milestones": Dict[str, MilestoneInfo],
                }
            }

        Notes:
            - Returns all data currently in memory for serialization.
            - Maintains data format even if any entity is empty.
            - Does not validate state integrity; use 'check_state_integrity' for that.
        """
        result = {
            "characters": self.characters,
            "inventories": self.inventories,
            "items": self.items,
            "game_worlds": self.game_worlds,
            "milestones": self.milestones,
        }
        if hasattr(self, "queued_world_changes"):
            result["queued_world_changes"] = copy.deepcopy(self.queued_world_changes)
        return {
            "success": True,
            "data": result
        }

    def check_state_integrity(self) -> dict:
        """
        Verify that the game state is internally consistent and satisfies min/max or relationship constraints.

        Returns:
            dict: {
                "success": True,
                "data": "Game state integrity verified."
            }
            OR
            {
                "success": False,
                "error": [list of problems found]
            }

        Game constraints checked:
        - PlayerCharacter health and stats within min/max (uses defaults if not specified elsewhere: health [0,9999], stats [0,999])
        - For every Inventory:
            * All item_ids in item_list exist in items.
            * Inventory character_id refers to existing PlayerCharacter.
            * (If enforced) Inventory cannot exceed 100 items.
        - For every Milestone:
            * Status 'in_progress' only if relevant to known player/game state (as stub: must be linked to known milestone and not 'orphans').
        - Relationships between world, milestones, inventory are valid.
        """
        errors = []
        HEALTH_MIN, HEALTH_MAX = 0, 9999
        STAT_MIN, STAT_MAX = 0, 999
        INVENTORY_SIZE_LIMIT = 100  # assumed; adjust if design specifies

        # Check player character stats
        for char_id, char in self.characters.items():
            h = char["health"]
            if not (HEALTH_MIN <= h <= HEALTH_MAX):
                errors.append(f"Player '{char_id}': health {h} is out of bounds [{HEALTH_MIN},{HEALTH_MAX}]")
            for stat_name, value in char.get("stats", {}).items():
                if not (STAT_MIN <= value <= STAT_MAX):
                    errors.append(f"Player '{char_id}': stat '{stat_name}' value {value} out of bounds [{STAT_MIN},{STAT_MAX}]")

        # Check inventories
        character_ids = set(self.characters.keys())
        for inv_id, inventory in self.inventories.items():
            # Inventory must belong to a known character
            char_id = inventory["character_id"]
            if char_id not in character_ids:
                errors.append(f"Inventory '{inv_id}' references unknown character '{char_id}'")
            # Inventory item count under limit
            item_list = inventory.get("item_list", [])
            if len(item_list) > INVENTORY_SIZE_LIMIT:
                errors.append(f"Inventory '{inv_id}' item count {len(item_list)} exceeds limit {INVENTORY_SIZE_LIMIT}")
            # All items exist
            for item in item_list:
                item_id = item.get("item_id")
                if not item_id or item_id not in self.items:
                    errors.append(f"Inventory '{inv_id}' contains nonexistent item_id '{item_id}'")
    
        # Check milestones
        valid_status = {"completed", "in_progress"}
        for milestone_id, milestone in self.milestones.items():
            # Status validity
            status = milestone.get("status")
            if status not in valid_status:
                errors.append(f"Milestone '{milestone_id}' has unknown status '{status}'")
            # 'in_progress' must only be for valid/known milestones (stub: must be linked to game, not orphan)
            if status == "in_progress":
                if not milestone.get("description"):
                    errors.append(f"Milestone '{milestone_id}' is 'in_progress' with no description")
                # Can add more checks if we track milestone-player relationships
        
        # Relationship checks (item in inventory item_list must exist in global items, covered above)
        # Could check world-milestones if more game rules given

        if errors:
            return {"success": False, "error": errors}
        else:
            return {"success": True, "data": "Game state integrity verified."}


    def save_game_state_to_json(self, file_path: str) -> dict:
        """
        Serialize and save the entire game state (all characters, inventories, items, world, and milestones)
        as a single JSON file.

        Args:
            file_path (str): Filesystem path to which to save the serialized JSON state.

        Returns:
            dict: {
                "success": True,
                "message": "Game state saved to <file_path>"
            }
            or
            {
                "success": False,
                "error": "Error message describing what went wrong"
            }

        Constraints:
            - Assumes current in-memory state is consistent.
            - File write errors may occur if path is invalid or permissions are denied.
        """
        state_data = {
            "characters": self.characters,
            "inventories": self.inventories,
            "items": self.items,
            "game_worlds": self.game_worlds,
            "milestones": self.milestones
        }

        try:
            actual_path = self._resolve_save_path(file_path)
            actual_path.parent.mkdir(parents=True, exist_ok=True)
            with open(actual_path, "w", encoding="utf-8") as f:
                json.dump(state_data, f, indent=2)
            return {"success": True, "message": f"Game state saved to {file_path}"}
        except Exception as e:
            return {"success": False, "error": f"Failed to save game state: {str(e)}"}


    def load_game_state_from_json(self, json_file_path: str) -> dict:
        """
        Restore the entire game state from a JSON file.

        Args:
            json_file_path (str): Path to the JSON file containing the saved game state.

        Returns:
            dict:
                {
                    'success': True,
                    'message': 'Game state loaded from JSON.'
                }
                OR
                {
                    'success': False,
                    'error': <error description>
                }

        Constraints:
            - All top-level entities must be present in the loaded file.
            - Relationships and integrity must be preserved.
            - If integrity fails after load, attempt automatic fixing if possible, or fail gracefully.
            - Does not modify state if file is unreadable or contains invalid structure.
        """
        required_keys = ['characters', 'inventories', 'items', 'game_worlds', 'milestones']
        resolved_path = self._resolve_load_path(json_file_path)
        if resolved_path is None:
            return {"success": False, "error": "JSON file not found"}

        try:
            with open(resolved_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            return {"success": False, "error": f"Error reading or parsing JSON: {e}"}

        # Check for presence of all required top-level keys
        if not all(key in data for key in required_keys):
            return {"success": False, "error": "Invalid game state file: missing required keys."}

        # Assignment (replace current state)
        self.characters = data.get('characters', {})
        self.inventories = data.get('inventories', {})
        self.items = data.get('items', {})
        self.game_worlds = data.get('game_worlds', {})
        self.milestones = data.get('milestones', {})

        # Optionally, check and attempt to fix/validate integrity just after loading
        if hasattr(self, "check_state_integrity"):
            integrity_check = self.check_state_integrity()
            if not integrity_check.get("success", False):
                # Try to fix if possible
                if hasattr(self, "fix_state_relationships"):
                    fix = self.fix_state_relationships()
                    if not fix.get("success", False):
                        return {"success": False, "error": "Loaded state is inconsistent and could not be auto-fixed."}
                else:
                    return {"success": False, "error": "Loaded state is inconsistent and cannot be used."}

        return {"success": True, "message": "Game state loaded from JSON."}

    def update_milestone_timestamp(self, milestone_id: str, new_timestamp: str) -> dict:
        """
        Update the 'timestamp' of a specified milestone.

        Args:
            milestone_id (str): The ID of the milestone to update.
            new_timestamp (str): The new timestamp string to set (e.g., ISO 8601).

        Returns:
            dict: 
                Success: { "success": True, "message": "Milestone timestamp updated." }
                Failure: { "success": False, "error": "Milestone not found." }

        Constraints:
            - The milestone with the given milestone_id must exist in the game state.
            - Only modifies the 'timestamp' field of the milestone.
        """
        if milestone_id not in self.milestones:
            return { "success": False, "error": "Milestone not found." }

        self.milestones[milestone_id]["timestamp"] = new_timestamp
        return { "success": True, "message": "Milestone timestamp updated." }

    def update_world_persistence(self) -> dict:
        """
        Apply all queued game world changes to the current game world state,
        synchronizing world variables, locations, areas, and NPC states. This prepares
        the state for serialization.

        Returns:
            dict:
                On success: {
                    "success": True,
                    "message": "All queued game world changes have been applied."
                }
                On failure: {
                    "success": False,
                    "error": str  # Description of what failed
                }

        Constraints:
            - If no queued world changes or no game worlds exist, treat as success with message.
            - Queued changes must reference existing world_state_id.
            - Queued changes must match structure of GameWorldInfo.
            - After applying, queued world changes are cleared.
        """
        if not hasattr(self, "queued_world_changes"):
            # If no changes have ever been queued, treat as no-op
            self.queued_world_changes = []

        if len(self.game_worlds) == 0:
            return {
                "success": False,
                "error": "No game world state available for persistent update."
            }

        applied = 0
        for change in list(self.queued_world_changes):
            if isinstance(change, (list, tuple)) and len(change) == 2:
                world_id, patch = change
            elif isinstance(change, dict) and "world_state_id" in change:
                world_id = change["world_state_id"]
                patch = {k: v for k, v in change.items() if k != "world_state_id"}
            elif isinstance(change, dict) and "target_world" in change:
                world_id = change["target_world"]
                patch = {k: v for k, v in change.items() if k != "target_world"}
            else:
                return {
                    "success": False,
                    "error": "Queued world changes are malformed."
                }
            resolved_world_id = self._resolve_world_key(world_id)
            if resolved_world_id is None:
                return {
                    "success": False,
                    "error": f"Queued changes reference unknown game world id '{world_id}'."
                }
            if not isinstance(patch, dict):
                return {
                    "success": False,
                    "error": "Queued change patch must be an object."
                }
            # Validate patch: only allow updates to known GameWorldInfo keys
            for key in patch:
                if key not in self.game_worlds[resolved_world_id]:
                    return {
                        "success": False,
                        "error": f"Queued change contains unknown world attribute '{key}'."
                    }
            # Apply the patch (shallow merge for updatable fields)
            self.game_worlds[resolved_world_id].update(patch)
            applied += 1

        # Clear applied changes
        self.queued_world_changes.clear()

        return {
            "success": True,
            "message": (
                f"All queued game world changes have been applied." if applied > 0
                else "No pending game world updates to apply."
            )
        }

    def fix_state_relationships(self) -> dict:
        """
        Update and repair references and relationships before save or load.
        Ensures:
          - Every Inventory is linked to an existing PlayerCharacter.
          - Every Inventory's items all exist in the global items list.
          - (Optionally) Extra checks for relationships between milestones/world and other entities.

        Returns:
            dict: {
                "success": True,
                "message": "All references and relationships updated and repaired."
            }
            or
            {
                "success": False,
                "error": "Description of failure"
            }
        """
        # 1. Repair inventory->character relationship
        valid_character_ids = set(self.characters.keys())

        # Gather orphan inventories first
        orphan_inventory_ids = [inv_id for inv_id, inv in self.inventories.items()
                                if inv["character_id"] not in valid_character_ids]

        for inv_id in orphan_inventory_ids:
            # Remove orphan inventory (as its character is missing)
            del self.inventories[inv_id]

        # 2. Repair inventory item lists: all items in the inventory must exist in self.items
        valid_item_ids = set(self.items.keys())

        for inv in self.inventories.values():
            fixed_item_list = []
            for item in inv["item_list"]:
                if item["item_id"] in valid_item_ids:
                    fixed_item_list.append(item)
            inv["item_list"] = fixed_item_list

        # (Optional) Further relationship repairing logic for milestones/gameworld could go here if required by schema.

        # Successfully completed
        return {
            "success": True,
            "message": "All references and relationships updated and repaired."
        }


class SinglePlayerGameStateManager(BaseEnv):
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
        tool_state_hints = {"check_state_integrity", "fix_state_relationships"}
        for key, value in init_config.items():
            if key in tool_state_hints:
                setattr(env, f"_{key}_state_hint", copy.deepcopy(value))
                continue
            if key == "queued_world_changes":
                setattr(env, key, SinglePlayerGameStateManager._normalize_queued_world_changes(value))
                continue
            setattr(env, key, copy.deepcopy(value))

    @staticmethod
    def _normalize_queued_world_changes(value):
        if value is None:
            return []
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return []
            try:
                value = json.loads(stripped)
            except Exception:
                match = re.fullmatch(
                    r"(?P<world>[A-Za-z0-9_]+):\s*add\s+unlocked_areas\s+\[(?P<areas>.*)\]",
                    stripped,
                )
                if match:
                    raw_areas = match.group("areas").strip()
                    areas = []
                    if raw_areas:
                        for part in raw_areas.split(","):
                            cleaned = part.strip().strip("'").strip('"')
                            if cleaned:
                                areas.append(cleaned)
                    return [(match.group("world"), {"unlocked_areas": areas})]
                return [{"__raw__": value}]
        if isinstance(value, dict):
            value = [value]
        if not isinstance(value, list):
            return [{"__raw__": copy.deepcopy(value)}]

        normalized = []
        for entry in value:
            if isinstance(entry, (list, tuple)) and len(entry) == 2 and isinstance(entry[0], str) and isinstance(entry[1], dict):
                normalized.append((entry[0], copy.deepcopy(entry[1])))
                continue
            if isinstance(entry, str):
                try:
                    entry = json.loads(entry)
                except Exception:
                    normalized.append({"__raw__": entry})
                    continue
            if isinstance(entry, dict):
                world_id = entry.get("world_state_id") or entry.get("target_world")
                if isinstance(world_id, str) and world_id:
                    patch = {
                        k: copy.deepcopy(v)
                        for k, v in entry.items()
                        if k not in {"world_state_id", "target_world"}
                    }
                    normalized.append((world_id, patch))
                else:
                    normalized.append({"__raw__": copy.deepcopy(entry)})
                continue
            normalized.append({"__raw__": copy.deepcopy(entry)})
        return normalized

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

    def get_player_character(self, **kwargs):
        return self._call_inner_tool('get_player_character', kwargs)

    def get_player_inventory(self, **kwargs):
        return self._call_inner_tool('get_player_inventory', kwargs)

    def get_inventory_items(self, **kwargs):
        return self._call_inner_tool('get_inventory_items', kwargs)

    def get_game_world_state(self, **kwargs):
        return self._call_inner_tool('get_game_world_state', kwargs)

    def get_player_milestones(self, **kwargs):
        return self._call_inner_tool('get_player_milestones', kwargs)

    def get_full_game_state(self, **kwargs):
        return self._call_inner_tool('get_full_game_state', kwargs)

    def check_state_integrity(self, **kwargs):
        return self._call_inner_tool('check_state_integrity', kwargs)

    def save_game_state_to_json(self, **kwargs):
        return self._call_inner_tool('save_game_state_to_json', kwargs)

    def load_game_state_from_json(self, **kwargs):
        return self._call_inner_tool('load_game_state_from_json', kwargs)

    def update_milestone_timestamp(self, **kwargs):
        return self._call_inner_tool('update_milestone_timestamp', kwargs)

    def update_world_persistence(self, **kwargs):
        return self._call_inner_tool('update_world_persistence', kwargs)

    def fix_state_relationships(self, **kwargs):
        return self._call_inner_tool('fix_state_relationships', kwargs)
