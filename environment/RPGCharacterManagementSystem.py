# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



class CharacterInfo(TypedDict):
    character_id: str
    name: str
    player_id: str
    level: int
    experience_points: int
    skill_points: int
    achievement_list: List[str]
    # These are references: IDs for inventory and equipment
    inventory: List[str]    # List of InventoryItemInfo IDs or item IDs
    equipment: List[str]    # List of EquipmentInfo IDs or slot names

class SkillInfo(TypedDict):
    skill_id: str
    skill_name: str
    skill_level: int
    character_id: str

class InventoryItemInfo(TypedDict):
    character_id: str
    item_id: str
    quantity: int

class EquipmentInfo(TypedDict):
    character_id: str
    slot: str
    item_id: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Character state: {character_id: CharacterInfo}
        self.characters: Dict[str, CharacterInfo] = {}
        # Registered skills: {skill_id: SkillInfo}
        self.skills: Dict[str, SkillInfo] = {}
        # Inventory items: {character_id: List[InventoryItemInfo]}
        self.inventories: Dict[str, List[InventoryItemInfo]] = {}
        # Equipment: {character_id: List[EquipmentInfo]}
        self.equipment: Dict[str, List[EquipmentInfo]] = {}

        # Constraints:
        # - Skill points and inventory quantities must be non-negative integers.
        # - Skill levels cannot exceed defined maximum for each skill.
        # - One item per equipment slot, per character.
        # - Characters must be tied to a valid player.

    def _sync_character_inventory_refs(self, character_id: str) -> None:
        character = self.characters.get(character_id)
        if character is None:
            return
        inventory_items = self.inventories.get(character_id, [])
        character["inventory"] = [
            item["item_id"]
            for item in inventory_items
            if item.get("quantity", 0) > 0
        ]

    def _sync_character_equipment_refs(self, character_id: str) -> None:
        character = self.characters.get(character_id)
        if character is None:
            return
        equipped_items = self.equipment.get(character_id, [])
        character["equipment"] = [item["item_id"] for item in equipped_items]

    def get_character_info(self, character_id: str) -> dict:
        """
        Fetch all base information for a character by character_id, including skill_points.

        Args:
            character_id (str): The ID of the character.

        Returns:
            dict:
                If character exists:
                    {
                        "success": True,
                        "data": CharacterInfo
                    }
                If character does not exist:
                    {
                        "success": False,
                        "error": "Character not found"
                    }
        """
        character = self.characters.get(character_id)
        if character is None:
            return {"success": False, "error": "Character not found"}
        return {"success": True, "data": character}

    def get_character_skill_points(self, character_id: str) -> dict:
        """
        Retrieve the current available skill points for a character.

        Args:
            character_id (str): The unique identifier of the character.

        Returns:
            dict: {
                "success": True,
                "data": int   # The number of available skill points
            }
            or
            {
                "success": False,
                "error": str  # Error message, e.g., character not found
            }

        Constraints:
            - Character must exist in the system.
        """
        if character_id not in self.characters:
            return {"success": False, "error": "Character does not exist"}
        skill_points = self.characters[character_id]["skill_points"]
        return {"success": True, "data": skill_points}

    def get_skills_by_character(self, character_id: str) -> dict:
        """
        List all skills (with names and levels) that a character possesses.

        Args:
            character_id (str): Unique identifier for the character.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": List[SkillInfo]  # List may be empty if the character has no skills
                    }
                On failure (character not found):
                    {
                        "success": False,
                        "error": "Character not found"
                    }

        Constraints:
            - character_id must exist in the RPG character management system.
        """
        if character_id not in self.characters:
            return { "success": False, "error": "Character not found" }

        result = [
            skill for skill in self.skills.values()
            if skill['character_id'] == character_id
        ]
        return { "success": True, "data": result }

    def get_character_inventory(self, character_id: str) -> dict:
        """
        Retrieve all inventory items (item IDs and quantities) for the specified character.

        Args:
            character_id (str): The unique ID of the character.

        Returns:
            dict: {
                "success": True,
                "data": List[InventoryItemInfo]   # Each element includes item_id, quantity, character_id
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - character_id must correspond to an existing character.
            - All returned quantities will be non-negative integers (guaranteed by state).
        """
        if character_id not in self.characters:
            return { "success": False, "error": "Character does not exist" }

        result = self.inventories.get(character_id, [])
        return { "success": True, "data": result }

    def get_character_equipment(self, character_id: str) -> dict:
        """
        Return the list of currently equipped items and their slots for a character.

        Args:
            character_id (str): The unique identifier of the character.

        Returns:
            dict: {
                "success": True,
                "data": List[EquipmentInfo]  # List of current equipped items for the character (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g., character does not exist
            }

        Constraints:
            - The character must exist in the system.
        """
        if character_id not in self.characters:
            return {"success": False, "error": "Character does not exist"}

        equipment_list = self.equipment.get(character_id, [])
        return {"success": True, "data": equipment_list}

    def get_skill_info(self, skill_id: str) -> dict:
        """
        Fetch details of a specific skill by its skill_id.

        Args:
            skill_id (str): The unique identifier for the skill.

        Returns:
            dict: On success:
                      { "success": True, "data": SkillInfo }
                  On failure:
                      { "success": False, "error": "Skill not found" }
        Constraints:
            - skill_id must exist in the system's skills dictionary.
        """
        if skill_id not in self.skills:
            return { "success": False, "error": "Skill not found" }
        return { "success": True, "data": self.skills[skill_id] }

    def get_inventory_item_info(self, character_id: str, item_id: str) -> dict:
        """
        Fetch specifics (quantity, item_id) about a single inventory item
        for a given character and item_id.

        Args:
            character_id (str): The ID of the character whose inventory is queried.
            item_id (str): The ID of the inventory item to fetch.

        Returns:
            dict:
                - On success: { "success": True, "data": InventoryItemInfo }
                - On failure: { "success": False, "error": "Inventory item not found" }

        Constraints:
            - Inventory quantities are expected to be non-negative, but this function only queries.
            - If character or item not found, returns error.
        """
        inventory = self.inventories.get(character_id)
        if not inventory:
            return { "success": False, "error": "Inventory item not found" }

        for item in inventory:
            if item["item_id"] == item_id:
                return { "success": True, "data": item }

        return { "success": False, "error": "Inventory item not found" }

    def get_equipment_slot_info(self, character_id: str, slot: str) -> dict:
        """
        Get info about what item (if any) is equipped in a given slot for a character.

        Args:
            character_id (str): The unique ID of the character.
            slot (str): The equipment slot to query (e.g., "head", "chest").

        Returns:
            dict: {
                "success": True,
                "data": EquipmentInfo | None  # EquipmentInfo if equipped, else None if nothing is equipped in the slot
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., character not found)
            }

        Constraints:
            - Equipment slots can hold only one item at a time.
            - Character must exist.
        """
        if character_id not in self.characters:
            return {"success": False, "error": "Character not found"}

        equipment_list = self.equipment.get(character_id, [])
        for eq in equipment_list:
            if eq["slot"] == slot:
                return {"success": True, "data": eq}

        # Slot is empty (no equipment in that slot)
        return {"success": True, "data": None}

    def update_skill_points(self, character_id: str, skill_points: int) -> dict:
        """
        Update a character's skill points. The skill points must remain a non-negative integer.

        Args:
            character_id (str): The unique identifier of the character.
            skill_points (int): The new value for the character's skill points.

        Returns:
            dict: {
                "success": True,
                "message": "Skill points for character <character_id> updated to <skill_points>."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The character must exist.
            - skill_points must be a non-negative integer.
        """
        if character_id not in self.characters:
            return {"success": False, "error": "Character does not exist."}
        if not isinstance(skill_points, int):
            return {"success": False, "error": "Skill points must be an integer."}
        if skill_points < 0:
            return {"success": False, "error": "Skill points must be a non-negative integer."}

        self.characters[character_id]["skill_points"] = skill_points
        return {
            "success": True,
            "message": f"Skill points for character {character_id} updated to {skill_points}."
        }

    def add_skill_to_character(self, character_id: str, skill_id: str, skill_name: str, skill_level: int) -> dict:
        """
        Add a new skill to a character. Creates a SkillInfo entry with the provided attributes.

        Args:
            character_id (str): The ID of the character to receive the skill.
            skill_id (str): The unique ID for the skill entry (must not already exist).
            skill_name (str): The name of the skill.
            skill_level (int): The initial level for the skill (must be >= 1).

        Returns:
            dict: {
                "success": True,
                "message": "Skill <skill_name> (ID=<skill_id>) added to character <character_id>"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - character_id must exist in self.characters.
            - skill_id must be unique in self.skills.
            - skill_level must be at least 1.
            - Skill must be attached to the correct character.
            - Skill level can't exceed domain max (not checked here as not specified).
        """
        # Check character existence
        if character_id not in self.characters:
            return { "success": False, "error": "Character does not exist" }

        # Check for skill ID uniqueness
        if skill_id in self.skills:
            return { "success": False, "error": "Skill ID already exists" }

        # Validate skill level
        if not isinstance(skill_level, int) or skill_level < 1:
            return { "success": False, "error": "Skill level must be >= 1" }

        # Create and add new skill
        new_skill = {
            "skill_id": skill_id,
            "skill_name": skill_name,
            "skill_level": skill_level,
            "character_id": character_id
        }
        self.skills[skill_id] = new_skill

        return {
            "success": True,
            "message": f"Skill {skill_name} (ID={skill_id}) added to character {character_id}"
        }

    def update_skill_level(self, skill_id: str, new_level: int) -> dict:
        """
        Change a skill's level for a character, not exceeding the maximum defined for the skill.

        Args:
            skill_id (str): The unique identifier of the skill to update.
            new_level (int): The desired new level for this skill.

        Returns:
            dict: {
                "success": True,
                "message": "Skill level updated successfully."
            }
            or
            {
                "success": False,
                "error": str  # Error reason if update cannot be performed
            }

        Constraints:
            - Skill with skill_id must exist.
            - new_level must be a non-negative integer.
            - new_level cannot exceed the maximum allowed for this skill (default: 10).
        """
        MAX_LEVEL = 10  # In production, should be loaded per skill_name/id.

        skill = self.skills.get(skill_id)
        if skill is None:
            return { "success": False, "error": "Skill does not exist" }
        if not isinstance(new_level, int) or new_level < 0:
            return { "success": False, "error": "Skill level must be a non-negative integer" }
        if new_level > MAX_LEVEL:
            return { "success": False, "error": f"Skill level cannot exceed maximum allowed level ({MAX_LEVEL})" }

        old_level = skill["skill_level"]
        skill["skill_level"] = new_level
        self.skills[skill_id] = skill

        return { "success": True, "message": f"Skill level updated from {old_level} to {new_level} successfully." }

    def add_inventory_item(self, character_id: str, item_id: str, quantity: int) -> dict:
        """
        Add a new item or increase quantity of an item in a character’s inventory.

        Args:
            character_id (str): The ID of the character to add the inventory item to.
            item_id (str): The item ID to add.
            quantity (int): Number of items to add (must be positive).

        Returns:
            dict: {
                "success": True,
                "message": str  # Success message with details,
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure,
            }

        Constraints:
            - 'quantity' must be a positive integer.
            - Inventory item quantities must remain non-negative.
            - Character must exist.
        """
        if character_id not in self.characters:
            return { "success": False, "error": "Character not found" }
        if not isinstance(quantity, int) or quantity <= 0:
            return { "success": False, "error": "Quantity must be a positive integer" }

        inventory = self.inventories.get(character_id, [])
        found = False
        for item in inventory:
            if item['item_id'] == item_id:
                item['quantity'] += quantity
                found = True
                final_quantity = item['quantity']
                break
        if not found:
            # Add new item
            new_item = {
                'character_id': character_id,
                'item_id': item_id,
                'quantity': quantity
            }
            inventory.append(new_item)
            final_quantity = quantity

        self.inventories[character_id] = inventory
        self._sync_character_inventory_refs(character_id)

        return {
            "success": True, 
            "message": f"Item {item_id} added to character {character_id}, quantity now {final_quantity}"
        }

    def remove_inventory_item(self, character_id: str, item_id: str, quantity: int) -> dict:
        """
        Decrease the quantity or remove an inventory item from a character.
        Ensures non-negative quantities and removes the item entry if quantity drops to zero.
    
        Args:
            character_id (str): The character's unique ID.
            item_id (str): The item ID to remove/decrement.
            quantity (int): The quantity to remove (must be positive integer).
    
        Returns:
            dict: 
                On success: { "success": True, "message": str }
                On failure: { "success": False, "error": str }
    
        Constraints:
            - Character must exist.
            - Item must exist in inventory.
            - Quantities must never become negative.
            - Quantity to remove must be positive integer.
        """
        # Check character exists
        if character_id not in self.characters:
            return {"success": False, "error": "Character does not exist"}

        if not isinstance(quantity, int) or quantity <= 0:
            return {"success": False, "error": "Quantity must be a positive integer"}
    
        inventory = self.inventories.get(character_id, [])
        found = False
        for idx, inv_item in enumerate(inventory):
            if inv_item["item_id"] == item_id:
                found = True
                if inv_item["quantity"] > quantity:
                    inv_item["quantity"] -= quantity
                    self._sync_character_inventory_refs(character_id)
                    return {
                        "success": True,
                        "message": f"Removed {quantity} of item '{item_id}' from character '{character_id}', {inv_item['quantity']} remaining."
                    }
                else:
                    # Remove all; delete the item entry
                    removed_qty = inv_item["quantity"]
                    del inventory[idx]
                    self.inventories[character_id] = inventory  # Update even though list mod is in place
                    self._sync_character_inventory_refs(character_id)
                    return {
                        "success": True,
                        "message": f"Removed all ({removed_qty}) of item '{item_id}' from character '{character_id}'. Item removed from inventory."
                    }
        if not found:
            return {"success": False, "error": "Item not found in character inventory"}

    def equip_item_to_slot(self, character_id: str, slot: str, item_id: str) -> dict:
        """
        Equip a specific item from the character's inventory into a given equipment slot.
        Only one item per slot is allowed.
    
        Args:
            character_id (str): The ID of the character to equip the item for.
            slot (str): The equipment slot to equip to (e.g., "helmet", "weapon").
            item_id (str): The ID of the item to equip.
    
        Returns:
            dict: {
                "success": True,
                "message": "Item <item_id> equipped to slot <slot> for character <character_id>"
            }
            or
            {
                "success": False,
                "error": "Reason for failure."
            }
    
        Constraints:
            - Character must exist.
            - Only one item per slot per character is allowed.
            - Item must exist in character's inventory and have quantity > 0.
        """
        # Check that character exists
        char = self.characters.get(character_id)
        if not char:
            return {"success": False, "error": "Character does not exist."}

        # Check if item exists in inventory and has quantity > 0
        inventory_items = self.inventories.get(character_id, [])
        found = False
        for inv in inventory_items:
            if inv['item_id'] == item_id:
                if inv['quantity'] <= 0:
                    return {"success": False, "error": "Item not available in inventory (quantity is zero)."}
                found = True
                break
        if not found:
            return {"success": False, "error": "Item not found in character's inventory."}

        # Equipment slot logic
        current_equipment_list = self.equipment.get(character_id, [])
        # Find if this slot already has an item
        for eq in current_equipment_list:
            if eq['slot'] == slot:
                return {"success": False, "error": f"Slot '{slot}' is already occupied. Unequip first."}

        # Equip the item
        new_equipment = EquipmentInfo(
            character_id=character_id,
            slot=slot,
            item_id=item_id
        )
        current_equipment_list.append(new_equipment)
        self.equipment[character_id] = current_equipment_list
        self._sync_character_equipment_refs(character_id)

        return {
            "success": True,
            "message": f"Item {item_id} equipped to slot {slot} for character {character_id}"
        }

    def unequip_item_from_slot(self, character_id: str, slot: str) -> dict:
        """
        Remove (unequip) the item from a specific equipment slot of a character.

        Args:
            character_id (str): The ID of the character.
            slot (str): The name of the equipment slot (e.g., "helmet", "weapon").

        Returns:
            dict:
                On success:
                    {"success": True, "message": "Item unequipped from slot <slot> for character <character_id>."}
                On failure:
                    {"success": False, "error": "<reason>"}

        Constraints:
            - Character must exist.
            - The specified slot must be currently equipped with an item. No effect if already empty.
        """
        if character_id not in self.characters:
            return { "success": False, "error": "Character does not exist." }

        equipment_list = self.equipment.get(character_id, [])
        # Find the equipment for this slot
        found = False
        for idx, equip_info in enumerate(equipment_list):
            if equip_info["slot"] == slot:
                found = True
                # Remove from equipment list
                del equipment_list[idx]
                self.equipment[character_id] = equipment_list
                self._sync_character_equipment_refs(character_id)
                return {
                    "success": True,
                    "message": f"Item unequipped from slot {slot} for character {character_id}."
                }

        if not found:
            return {
                "success": False,
                "error": f"No item equipped in slot {slot} for character {character_id}."
            }

    def update_character_achievements(
        self, 
        character_id: str, 
        add: List[str] = None, 
        remove: List[str] = None
    ) -> dict:
        """
        Add or remove achievements in a character's achievement list.

        Args:
            character_id (str): The character whose achievements are to be modified.
            add (List[str], optional): Achievements (IDs/names) to add. Default: None.
            remove (List[str], optional): Achievements (IDs/names) to remove. Default: None.

        Returns:
            dict: {
                "success": True,
                "message": "Updated achievements for character <character_id>."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Character must exist (valid character_id).
            - Achievement list should not contain duplicates.
            - If 'add' or 'remove' includes achievements already in correct state, they're ignored.
        """
        if character_id not in self.characters:
            return { "success": False, "error": "Character not found" }

        add = add or []
        remove = remove or []
        achievement_set = set(self.characters[character_id]["achievement_list"])

        # Add new achievements
        for ach in add:
            achievement_set.add(ach)

        # Remove specified achievements
        for ach in remove:
            achievement_set.discard(ach)

        self.characters[character_id]["achievement_list"] = list(achievement_set)
        return {
            "success": True,
            "message": f"Updated achievements for character {character_id}."
        }

    def update_character_level_or_exp(
        self,
        character_id: str,
        level: int = None,
        experience_points: int = None
    ) -> dict:
        """
        Update the specified character's level and/or experience points.

        Args:
            character_id (str): The ID of the character to update.
            level (int, optional): New level to set (must be non-negative).
            experience_points (int, optional): New experience points to set (must be non-negative).

        Returns:
            dict: {
                "success": True,
                "message": "Character level/experience updated"
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g. character not found, invalid values, etc.
            }

        Constraints:
            - character_id must point to an existing character.
            - Level and experience_points, if supplied, must be integers >= 0.
            - At least one of level or experience_points must be provided.
        """
        if character_id not in self.characters:
            return { "success": False, "error": "Character does not exist" }

        if level is None and experience_points is None:
            return { "success": False, "error": "No update value provided (level or experience_points required)" }

        if level is not None:
            if not isinstance(level, int) or level < 0:
                return { "success": False, "error": "Level must be a non-negative integer" }
            self.characters[character_id]["level"] = level

        if experience_points is not None:
            if not isinstance(experience_points, int) or experience_points < 0:
                return { "success": False, "error": "Experience points must be a non-negative integer" }
            self.characters[character_id]["experience_points"] = experience_points

        return { "success": True, "message": "Character level/experience updated" }


class RPGCharacterManagementSystem(BaseEnv):
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

    def get_character_info(self, **kwargs):
        return self._call_inner_tool('get_character_info', kwargs)

    def get_character_skill_points(self, **kwargs):
        return self._call_inner_tool('get_character_skill_points', kwargs)

    def get_skills_by_character(self, **kwargs):
        return self._call_inner_tool('get_skills_by_character', kwargs)

    def get_character_inventory(self, **kwargs):
        return self._call_inner_tool('get_character_inventory', kwargs)

    def get_character_equipment(self, **kwargs):
        return self._call_inner_tool('get_character_equipment', kwargs)

    def get_skill_info(self, **kwargs):
        return self._call_inner_tool('get_skill_info', kwargs)

    def get_inventory_item_info(self, **kwargs):
        return self._call_inner_tool('get_inventory_item_info', kwargs)

    def get_equipment_slot_info(self, **kwargs):
        return self._call_inner_tool('get_equipment_slot_info', kwargs)

    def update_skill_points(self, **kwargs):
        return self._call_inner_tool('update_skill_points', kwargs)

    def add_skill_to_character(self, **kwargs):
        return self._call_inner_tool('add_skill_to_character', kwargs)

    def update_skill_level(self, **kwargs):
        return self._call_inner_tool('update_skill_level', kwargs)

    def add_inventory_item(self, **kwargs):
        return self._call_inner_tool('add_inventory_item', kwargs)

    def remove_inventory_item(self, **kwargs):
        return self._call_inner_tool('remove_inventory_item', kwargs)

    def equip_item_to_slot(self, **kwargs):
        return self._call_inner_tool('equip_item_to_slot', kwargs)

    def unequip_item_from_slot(self, **kwargs):
        return self._call_inner_tool('unequip_item_from_slot', kwargs)

    def update_character_achievements(self, **kwargs):
        return self._call_inner_tool('update_character_achievements', kwargs)

    def update_character_level_or_exp(self, **kwargs):
        return self._call_inner_tool('update_character_level_or_exp', kwargs)
