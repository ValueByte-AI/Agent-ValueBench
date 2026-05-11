# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict, Any
import uuid
from datetime import datetime



class UserInfo(TypedDict):
    _id: str
    name: str
    dietary_goals: Dict[str, Any]  # e.g., {'calories': 2000, 'protein': 150, ...}
    profile_data: Dict[str, Any]   # Additional custom profile info

class FoodItemInfo(TypedDict):
    food_item_id: str
    name: str
    nutritional_info: Dict[str, Any]  # e.g., {'calories': 120, 'protein': 6.5, ...}

class MealEntryInfo(TypedDict):
    meal_entry_id: str
    user_id: str
    timestamp: str
    meal_type: str   # e.g., breakfast, lunch, dinner, snack
    no: int

class MealEntryItemInfo(TypedDict):
    meal_entry_id: str
    food_item_id: str
    quantity: float
    un: str          # unit of the food (e.g., 'g', 'ml', etc.)

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for personal diet & nutrition tracking.
        """

        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # Food items: {food_item_id: FoodItemInfo}
        self.food_items: Dict[str, FoodItemInfo] = {}

        # Meal entries: {meal_entry_id: MealEntryInfo}
        self.meal_entries: Dict[str, MealEntryInfo] = {}

        # Meal entry items: {meal_entry_id: [MealEntryItemInfo, ...]}
        self.meal_entry_items: Dict[str, List[MealEntryItemInfo]] = {}

        # Constraints:
        # - Users can only edit or delete their own meal entries.
        # - Food items selected for entry must exist in the food item database (or be created as custom items).
        # - Nutritional goals (if set) are user-specific and tracked against sums of logged nutrition over periods (e.g., daily).
        # - Each meal entry must have at least one associated MealEntryItem.

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user profile information and dietary goals by user ID.

        Args:
            user_id (str): The unique identifier for the user.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo  # The user's profile and dietary goals
            }
            or
            {
                "success": False,
                "error": str  # "User not found" if ID does not exist
            }
        """
        user = self.users.get(user_id)
        if user is None:
            return {"success": False, "error": "User not found"}

        return {"success": True, "data": user}

    def get_user_by_name(self, name: str) -> dict:
        """
        Retrieve user info using the user's name.

        Args:
            name (str): User's name to look up.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo  # whole user info dict
            }
            or
            {
                "success": False,
                "error": str  # "User not found" if no such user
            }

        Notes/Constraints:
            - Will return the first user with the matching name (names may not be unique).
        """
        for user in self.users.values():
            if user["name"] == name:
                return { "success": True, "data": user }
        return { "success": False, "error": "User not found" }

    def list_user_meal_entries(self, user_id: str) -> dict:
        """
        List all meal entries (with timestamps and types) for a given user.

        Args:
            user_id (str): The unique identifier for the user.

        Returns:
            dict:
                success: True if query succeeded, False if not.
                data: List[MealEntryInfo] (may be empty) if succeeded.
                error: Reason if not successful.

        Constraints:
            - The user_id must exist in the system.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        meal_entries = [
            meal_entry for meal_entry in self.meal_entries.values()
            if meal_entry["user_id"] == user_id
        ]

        return {"success": True, "data": meal_entries}

    def get_meal_entry_by_id(self, meal_entry_id: str) -> dict:
        """
        Retrieve full details of a meal entry by its ID.

        Args:
            meal_entry_id (str): The unique ID of the meal entry.

        Returns:
            dict: {
                "success": True,
                "data": MealEntryInfo
            }
            or
            {
                "success": False,
                "error": str  # "Meal entry not found"
            }

        Constraints:
            - The meal_entry_id must exist in the system.
        """
        meal_entry = self.meal_entries.get(meal_entry_id)
        if not meal_entry:
            return {"success": False, "error": "Meal entry not found"}

        return {"success": True, "data": meal_entry}

    def list_meal_items_for_entry(self, meal_entry_id: str) -> dict:
        """
        List all MealEntryItems (food, quantity, unit) for a given MealEntry.

        Args:
            meal_entry_id (str): The ID of the meal entry whose items are to be listed.
    
        Returns:
            dict:
                success: True and data (list of MealEntryItemInfo) if found.
                success: False and error message if not found or invalid meal entry.

        Constraints:
            - Meal entry must exist.
            - Each valid meal entry should have at least one associated MealEntryItem.
        """
        if meal_entry_id not in self.meal_entries:
            return { "success": False, "error": "Meal entry does not exist" }
    
        items = self.meal_entry_items.get(meal_entry_id)
        if items is None or not isinstance(items, list) or len(items) == 0:
            # This should not normally happen if constraints are strongly enforced,
            # but guard against missing or empty in-memory data.
            return { "success": False, "error": "No meal items found for this meal entry" }
    
        return { "success": True, "data": items }

    def get_food_item_by_name(self, name: str, fuzzy: bool = False) -> dict:
        """
        Retrieve FoodItem record(s) by name.

        Args:
            name (str): The name to search for (case-insensitive).
            fuzzy (bool, optional): If True, perform case-insensitive substring match (fuzzy).
                                   If False (default), match exact name (case-insensitive).

        Returns:
            dict:
                - { "success": True, "data": List[FoodItemInfo] }
                    (List is empty if no matches)
                
        Constraints:
            - Food items can be searched by any name, exact (default) or fuzzy.
            - Match is always case-insensitive.
        """
        matches = []
        name_lower = name.strip().lower()
        for food in self.food_items.values():
            food_name_lower = food["name"].strip().lower()
            if (fuzzy and name_lower in food_name_lower) or (not fuzzy and name_lower == food_name_lower):
                matches.append(food)
        return { "success": True, "data": matches }

    def get_food_item_by_id(self, food_item_id: str) -> dict:
        """
        Retrieve food item details by its unique ID.

        Args:
            food_item_id (str): The unique identifier of the food item.

        Returns:
            dict: {
                "success": True,
                "data": FoodItemInfo,  # The dictionary containing food item details.
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., food item not found.
            }
        """
        food_item = self.food_items.get(food_item_id)
        if not food_item:
            return {"success": False, "error": "Food item not found."}
        return {"success": True, "data": food_item}

    def list_food_items(self) -> dict:
        """
        List all available food items in the system/database.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[FoodItemInfo],  # All FoodItemInfo records (may be empty)
            }

        Constraints:
            - No user/context restrictions for listing foods.
            - Handles empty database scenario gracefully.

        Edge Cases:
            - If no food items in the system, returns empty list but success True.
        """
        all_items = list(self.food_items.values()) if self.food_items else []
        return {
            "success": True,
            "data": all_items
        }

    def get_nutritional_info_for_food(self, food_item_id: str) -> dict:
        """
        Retrieve nutritional information for a given food item by its ID.

        Args:
            food_item_id (str): The unique identifier for the food item.

        Returns:
            dict: {
                "success": True,
                "data": nutritional_info (dict)  # Nutritional values, e.g., {'calories': 120, ...}
            }
            or
            {
                "success": False,
                "error": str  # e.g., Food item not found
            }

        Constraints:
            - The food item must exist in the food item database.
        """
        food_item = self.food_items.get(food_item_id)
        if not food_item:
            return { "success": False, "error": "Food item not found" }
        # If nutritional_info field is somehow missing, treat as not found
        nutritional_info = food_item.get("nutritional_info")
        if nutritional_info is None:
            return { "success": False, "error": "Nutritional information is missing for the given food item." }
        return { "success": True, "data": nutritional_info }

    def get_user_nutritional_goals(self, user_id: str) -> dict:
        """
        Retrieve current dietary (nutritional) goals set by the specified user.

        Args:
            user_id (str): Unique identifier for the user.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": Dict[str, Any]  # Dietary goals (may be empty dict)
                    }
                - On failure:
                    {
                        "success": False,
                        "error": "User not found"
                    }

        Constraints:
            - User must exist in the system.
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }
        # 'dietary_goals' is expected to be present as per UserInfo structure (possibly empty).
        return { "success": True, "data": user.get("dietary_goals", {}) }

    def get_daily_nutrition_summary(self, user_id: str, date: str) -> dict:
        """
        Retrieve the sum of logged nutrition for the user for a specific day.

        Args:
            user_id (str): The user whose daily summary to retrieve.
            date (str): The target day, format 'YYYY-MM-DD'.

        Returns:
            dict:
                {
                    "success": True,
                    "data": Dict[str, float],    # sum of each nutrient, e.g. {"calories": 1410.0, "protein": 56.2, ...}
                }
                or
                {
                    "success": False,
                    "error": str     # e.g., "User does not exist"
                }

        Constraints:
            - User must exist.
            - Only meal entries from the specified day for this user are considered.
            - Only valid food items are summed; missing food items are ignored.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        # Collect all meal entries for this user on the specified date.
        relevant_meal_ids = [
            meal_entry_id for meal_entry_id, meal_info in self.meal_entries.items()
            if meal_info["user_id"] == user_id and meal_info["timestamp"][:10] == date
        ]

        nutrition_totals = {}

        for meal_id in relevant_meal_ids:
            for item in self.meal_entry_items.get(meal_id, []):
                food_item_id = item["food_item_id"]
                quantity = item["quantity"]

                food_info = self.food_items.get(food_item_id)
                if not food_info or not food_info.get("nutritional_info"):
                    continue  # skip missing food items

                for nutrient_name, per_unit_value in food_info["nutritional_info"].items():
                    total_value = per_unit_value * quantity   # Assuming per 1 unit as recorded
                    if nutrient_name not in nutrition_totals:
                        nutrition_totals[nutrient_name] = 0.0
                    nutrition_totals[nutrient_name] += total_value

        # If no data, return zeros for all known nutrients (from user's dietary goals if set)
        if not nutrition_totals and self.users[user_id].get("dietary_goals"):
            for k in self.users[user_id]["dietary_goals"].keys():
                nutrition_totals[k] = 0.0

        return { "success": True, "data": nutrition_totals }

    def create_meal_entry(self, user_id: str, meal_type: str, timestamp: str) -> dict:
        """
        Create a new MealEntry record for a user with the given type and timestamp.

        Args:
            user_id (str): Target user's ID.
            meal_type (str): Type of the meal (e.g., breakfast, lunch, dinner, snack).
            timestamp (str): ISO8601 or datetime string for when meal occurred.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Meal entry created",
                        "meal_entry_id": <generated_id>
                    }
                On failure:
                    {
                        "success": False,
                        "error": <description>
                    }

        Constraints:
            - user_id must exist.
            - meal_type and timestamp must be non-empty.
            - meal_entry_id must be unique.
            - Each meal entry will eventually require at least one MealEntryItem (not enforced here).
        """
        # User existence check
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }
        if not meal_type or not isinstance(meal_type, str):
            return { "success": False, "error": "Invalid meal type" }
        if not timestamp or not isinstance(timestamp, str):
            return { "success": False, "error": "Invalid timestamp" }

        # Generate unique meal_entry_id (simple monotonic approach or UUID)
        meal_entry_id = str(uuid.uuid4())
        while meal_entry_id in self.meal_entries:
            meal_entry_id = str(uuid.uuid4())  # Extremely unlikely collision

        # Calculate 'no' (meal index for user that day)
        try:
            ts_day = timestamp.split("T")[0]  # YYYY-MM-DD from ISO
        except Exception:
            # Fallback: use timestamp as string
            ts_day = timestamp

        # Count how many entries user already has on that date
        existing_meals = [
            entry for entry in self.meal_entries.values()
            if entry["user_id"] == user_id and entry["timestamp"].startswith(ts_day)
        ]
        meal_no = 1 + len(existing_meals)

        # Create entry
        entry = {
            "meal_entry_id": meal_entry_id,
            "user_id": user_id,
            "timestamp": timestamp,
            "meal_type": meal_type,
            "no": meal_no
        }
        self.meal_entries[meal_entry_id] = entry
        self.meal_entry_items[meal_entry_id] = []  # Initialize with no items yet

        return {
            "success": True,
            "message": "Meal entry created",
            "meal_entry_id": meal_entry_id
        }

    def add_item_to_meal_entry(
        self,
        meal_entry_id: str,
        food_item_id: str,
        quantity: float,
        un: str
    ) -> dict:
        """
        Add a MealEntryItem (food item, quantity, unit) to an existing MealEntry.

        Args:
            meal_entry_id (str): The meal entry to add to (must exist).
            food_item_id (str): The food item to add (must exist).
            quantity (float): The quantity of food (should be >0).
            un (str): Unit of the quantity (e.g., 'g', 'ml').

        Returns:
            dict: {
                "success": True,
                "message": "Meal entry item added."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - meal_entry_id must exist.
            - food_item_id must exist.
            - If no meal_entry_items[meal_entry_id] list exists, create it.
            - It is sensible to require quantity > 0.
        """
        if meal_entry_id not in self.meal_entries:
            return { "success": False, "error": "Meal entry does not exist." }
        if food_item_id not in self.food_items:
            return { "success": False, "error": "Food item does not exist." }
        if not isinstance(quantity, (int, float)) or quantity <= 0:
            return { "success": False, "error": "Quantity must be a positive number." }
        if not un or not isinstance(un, str):
            return { "success": False, "error": "Unit must be a non-empty string." }

        # Prepare the new MealEntryItem
        new_item = {
            "meal_entry_id": meal_entry_id,
            "food_item_id": food_item_id,
            "quantity": float(quantity),
            "un": un
        }
        if meal_entry_id not in self.meal_entry_items:
            self.meal_entry_items[meal_entry_id] = []
        self.meal_entry_items[meal_entry_id].append(new_item)
        return { "success": True, "message": "Meal entry item added." }

    def create_food_item(
        self,
        food_item_id: str,
        name: str,
        nutritional_info: dict
    ) -> dict:
        """
        Add a new food item to the food item database.

        Args:
            food_item_id (str): Unique identifier for the new food item.
            name (str): Name of the food item.
            nutritional_info (dict): Dictionary of nutrition information (e.g., {'calories': 120, 'protein': 6.5, ...}).

        Returns:
            dict:
                - On success: { "success": True, "message": "Food item created" }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - food_item_id must be unique.
            - Name must be a non-empty string.
            - nutritional_info must be provided as a dictionary.
        """
        if not isinstance(food_item_id, str) or not food_item_id:
            return { "success": False, "error": "Food item ID is required and must be a non-empty string" }
        if food_item_id in self.food_items:
            return { "success": False, "error": "Food item ID already exists" }
        if not isinstance(name, str) or not name.strip():
            return { "success": False, "error": "Food item name is required" }
        if not isinstance(nutritional_info, dict) or not nutritional_info:
            return { "success": False, "error": "Nutritional info is required" }

        # Prepare food item info
        new_food_item: FoodItemInfo = {
            "food_item_id": food_item_id,
            "name": name.strip(),
            "nutritional_info": nutritional_info
        }
        self.food_items[food_item_id] = new_food_item
        return { "success": True, "message": "Food item created" }

    def edit_meal_entry(
        self,
        meal_entry_id: str,
        user_id: str,
        timestamp: str = None,
        meal_type: str = None,
        no: int = None
    ) -> dict:
        """
        Edit details (e.g., meal_type, timestamp, no) of a MealEntry owned by the user.

        Args:
            meal_entry_id (str): ID of the meal entry to edit.
            user_id (str): ID of the user requesting the edit (must own entry).
            timestamp (str, optional): New timestamp.
            meal_type (str, optional): New meal type (e.g., breakfast, lunch).
            no (int, optional): Session number or similar.

        Returns:
            dict: {"success": True, "message": "..."} on success,
                  {"success": False, "error": "..."} on failure.

        Constraints:
            - Only allow the user who owns the meal entry to edit it.
            - Meal entry must exist.
            - At least one field (timestamp, meal_type, no) must be specified for update (optional for no-op).
        """
        # Check meal entry existence
        entry = self.meal_entries.get(meal_entry_id)
        if not entry:
            return {"success": False, "error": "Meal entry does not exist"}

        # Check user ownership
        if entry["user_id"] != user_id:
            return {"success": False, "error": "Permission denied: not owner of this meal entry"}

        # Check for user existence (optional, but good practice)
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        # Update fields if provided
        any_updated = False
        if timestamp is not None:
            entry["timestamp"] = timestamp
            any_updated = True
        if meal_type is not None:
            entry["meal_type"] = meal_type
            any_updated = True
        if no is not None:
            entry["no"] = no
            any_updated = True

        if not any_updated:
            # No error here; just no update needed
            return {"success": True, "message": "No fields updated for meal entry"}

        self.meal_entries[meal_entry_id] = entry  # Write-back for safety (though dicts are mutable)
        return {"success": True, "message": "Meal entry updated successfully"}

    def edit_meal_entry_item(
        self,
        user_id: str,
        meal_entry_id: str,
        old_food_item_id: str,
        new_food_item_id: str = None,
        quantity: float = None,
        un: str = None
    ) -> dict:
        """
        Edit a food item, quantity, or unit for an existing MealEntryItem.

        Args:
            user_id (str): ID of the user performing the edit.
            meal_entry_id (str): ID of the meal entry containing the item.
            old_food_item_id (str): Food item ID of the item to be edited.
            new_food_item_id (str, optional): New food item ID to update to (must exist in food item DB).
            quantity (float, optional): New quantity for this meal item.
            un (str, optional): New unit string for this meal item (e.g., 'g', 'ml').

        Returns:
            dict: {
                "success": True,
                "message": "Meal entry item updated"
            }
            or
            {
                "success": False,
                "error": <str>
            }
        Constraints:
            - Only the owner of the meal entry can edit items.
            - Food item being edited must exist in meal_entry_items for the meal entry.
            - If changing food_item_id, the new one must exist in food_items and be unique within the meal entry.
        """

        # Check that meal entry exists
        meal_entry = self.meal_entries.get(meal_entry_id)
        if not meal_entry:
            return { "success": False, "error": "Meal entry does not exist" }

        # Check user owns the entry
        if meal_entry["user_id"] != user_id:
            return { "success": False, "error": "User does not own this meal entry" }

        # Check meal_entry_items exist for entry
        items = self.meal_entry_items.get(meal_entry_id, [])
        if not items:
            return { "success": False, "error": "No meal items recorded for this entry" }

        # Find the target item to edit
        target_item_idx = None
        for idx, item in enumerate(items):
            if item["food_item_id"] == old_food_item_id:
                target_item_idx = idx
                break
        if target_item_idx is None:
            return { "success": False, "error": "Meal item not found for this meal entry" }

        # Target item to update
        target_item = items[target_item_idx]

        # Determine new food_item_id, quantity, unit
        updated_food_item_id = new_food_item_id if new_food_item_id is not None else target_item["food_item_id"]
        updated_quantity = quantity if quantity is not None else target_item["quantity"]
        updated_un = un if un is not None else target_item["un"]

        # If changing food_item_id, check new exists and is not duplicate within same entry
        if updated_food_item_id != old_food_item_id:
            if updated_food_item_id not in self.food_items:
                return { "success": False, "error": "Requested food item does not exist in database" }
            # Ensure unique within the same meal entry
            if any(
                i["food_item_id"] == updated_food_item_id and idx != target_item_idx
                for idx, i in enumerate(items)
            ):
                return { "success": False, "error": "This food item is already added to the meal entry" }

        # Validate quantity (optional, but negative makes no sense)
        if updated_quantity <= 0:
            return { "success": False, "error": "Quantity must be positive" }
        if not isinstance(updated_un, str) or not updated_un:
            return { "success": False, "error": "Unit must be a non-empty string" }

        # Apply changes
        items[target_item_idx] = {
            "meal_entry_id": meal_entry_id,
            "food_item_id": updated_food_item_id,
            "quantity": updated_quantity,
            "un": updated_un
        }
        self.meal_entry_items[meal_entry_id] = items

        return { "success": True, "message": "Meal entry item updated" }

    def remove_meal_entry_item(self, meal_entry_id: str, food_item_id: str, current_user_id: str) -> dict:
        """
        Remove a specific MealEntryItem (identified by meal_entry_id and food_item_id)
        from a MealEntry, ensuring at least one item remains.
        Only allowed if the current user owns the meal entry.

        Args:
            meal_entry_id (str): The ID of the meal entry to modify.
            food_item_id (str): The food item to remove from the meal entry.
            current_user_id (str): The user requesting the removal (for ownership check).

        Returns:
            dict: {
                "success": True,
                "message": "Meal entry item removed."
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Must not leave the meal entry with zero items.
            - Only the meal entry owner can remove items.
        """
        meal_entry = self.meal_entries.get(meal_entry_id)
        if not meal_entry:
            return {"success": False, "error": "Meal entry does not exist."}

        if meal_entry["user_id"] != current_user_id:
            return {"success": False, "error": "Permission denied. Users can only modify their own meal entries."}

        items = self.meal_entry_items.get(meal_entry_id, [])
        if not items:
            return {"success": False, "error": "No items found for this meal entry."}

        # Find the index of the item to remove
        idx_to_remove = None
        for idx, item in enumerate(items):
            if item["food_item_id"] == food_item_id:
                idx_to_remove = idx
                break

        if idx_to_remove is None:
            return {"success": False, "error": "Food item not found in this meal entry."}

        if len(items) <= 1:
            return {"success": False, "error": "Each meal entry must have at least one item. Cannot remove the last item."}

        # Remove the item
        del items[idx_to_remove]
        self.meal_entry_items[meal_entry_id] = items  # Update

        return {"success": True, "message": "Meal entry item removed."}

    def delete_meal_entry(self, user_id: str, meal_entry_id: str) -> dict:
        """
        Delete a MealEntry (with given meal_entry_id) owned by the given user_id.
        Also removes all associated MealEntryItems.

        Args:
            user_id (str): The user performing the delete (must be the owner).
            meal_entry_id (str): The MealEntry to delete.

        Returns:
            dict:
                On success: { "success": True, "message": "Meal entry deleted successfully." }
                On error:   { "success": False, "error": <reason> }
    
        Constraints:
            - Users can only delete their own meal entries.
            - All associated MealEntryItems must be removed.
            - Safe if no items exist.
        """
        meal_entry = self.meal_entries.get(meal_entry_id)
        if meal_entry is None:
            return { "success": False, "error": "Meal entry does not exist." }
        if meal_entry["user_id"] != user_id:
            return { "success": False, "error": "Permission denied: cannot delete another user's meal entry." }

        # Delete MealEntry
        del self.meal_entries[meal_entry_id]

        # Delete associated MealEntryItems
        if meal_entry_id in self.meal_entry_items:
            del self.meal_entry_items[meal_entry_id]

        return { "success": True, "message": "Meal entry deleted successfully." }

    def update_user_dietary_goals(self, user_id: str, new_goals: dict) -> dict:
        """
        Set or modify the dietary/nutrition goals for a user.

        Args:
            user_id (str): The unique identifier of the user.
            new_goals (dict): The new dietary/nutritional goals (e.g., {"calories": 2000, "protein": 150, ...}).

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Dietary goals updated for user id <user_id>"
                    }
                On failure:
                    {
                        "success": False,
                        "error": "User not found"
                    }
        Constraints:
            - The user must exist in the system.
            - new_goals can be any dictionary and will fully replace the user's previous dietary_goals.
        """
        user = self.users.get(user_id)
        if not user:
            return { "success": False, "error": "User not found" }
    
        user["dietary_goals"] = new_goals
        return { "success": True, "message": f"Dietary goals updated for user id {user_id}" }

    def update_food_item(
        self, 
        food_item_id: str, 
        name: str = None, 
        nutritional_info: dict = None
    ) -> dict:
        """
        Modify the name and/or nutritional info of an existing food item.
    
        Args:
            food_item_id (str): The ID of the food item to modify.
            name (str, optional): New name for the food item.
            nutritional_info (dict, optional): New nutritional info (replaces or updates existing).
        
        Returns:
            dict:
                - If success: {"success": True, "message": "Food item updated successfully."}
                - If failure: {"success": False, "error": <reason>}
    
        Constraints:
            - Food item with food_item_id must already exist.
            - At least one of 'name' or 'nutritional_info' must be provided.
            - If provided, nutritional_info must be a dictionary.
        """
        if food_item_id not in self.food_items:
            return {"success": False, "error": "Food item does not exist."}

        if name is None and nutritional_info is None:
            return {"success": False, "error": "No update parameters provided."}

        updated = False
        if name is not None:
            self.food_items[food_item_id]["name"] = name
            updated = True
        if nutritional_info is not None:
            if not isinstance(nutritional_info, dict):
                return {"success": False, "error": "nutritional_info must be a dictionary."}
            # Update all fields (overwrite or upsert each key)
            self.food_items[food_item_id]["nutritional_info"].update(nutritional_info)
            updated = True

        if updated:
            return {"success": True, "message": "Food item updated successfully."}
        else:
            return {"success": False, "error": "No valid update parameters provided."}


    def duplicate_meal_entry(self, meal_entry_id: str, user_id: str) -> dict:
        """
        Create a new MealEntry by copying an existing one for convenience.

        Args:
            meal_entry_id (str): ID of the MealEntry to duplicate.
            user_id (str): ID of user requesting duplication.

        Returns:
            dict: {
                "success": True,
                "message": "Meal entry duplicated.",
                "new_meal_entry_id": str,
            }
            or
            {
                "success": False,
                "error": str,
            }

        Constraints:
            - Users can only duplicate their own meal entries.
            - Original meal entry must exist and have at least one associated MealEntryItem.
        """

        # Check if user exists
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}
    
        # Check if meal entry exists
        orig_entry = self.meal_entries.get(meal_entry_id)
        if not orig_entry:
            return {"success": False, "error": "Source meal entry does not exist"}
    
        # Check permission
        if orig_entry["user_id"] != user_id:
            return {"success": False, "error": "Permission denied: cannot duplicate another user's meal entry"}
    
        # Check meal items exist
        orig_items = self.meal_entry_items.get(meal_entry_id, [])
        if not orig_items:
            return {"success": False, "error": "Source meal entry has no items"}
    
        # Generate new meal_entry_id
        new_meal_entry_id = str(uuid.uuid4())
    
        # Duplicate MealEntryInfo
        new_entry = orig_entry.copy()
        new_entry["meal_entry_id"] = new_meal_entry_id
        # Optionally set timestamp to now (repeat for today?); for now, keep original timestamp
        new_entry["timestamp"] = datetime.now().isoformat()
    
        self.meal_entries[new_meal_entry_id] = new_entry
    
        # Duplicate MealEntryItemInfo
        new_items = []
        for item in orig_items:
            new_item = item.copy()
            new_item["meal_entry_id"] = new_meal_entry_id
            new_items.append(new_item)
        self.meal_entry_items[new_meal_entry_id] = new_items

        return {
            "success": True,
            "message": "Meal entry duplicated.",
            "new_meal_entry_id": new_meal_entry_id
        }


class PersonalDietNutritionTracker(BaseEnv):
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

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def get_user_by_name(self, **kwargs):
        return self._call_inner_tool('get_user_by_name', kwargs)

    def list_user_meal_entries(self, **kwargs):
        return self._call_inner_tool('list_user_meal_entries', kwargs)

    def get_meal_entry_by_id(self, **kwargs):
        return self._call_inner_tool('get_meal_entry_by_id', kwargs)

    def list_meal_items_for_entry(self, **kwargs):
        return self._call_inner_tool('list_meal_items_for_entry', kwargs)

    def get_food_item_by_name(self, **kwargs):
        return self._call_inner_tool('get_food_item_by_name', kwargs)

    def get_food_item_by_id(self, **kwargs):
        return self._call_inner_tool('get_food_item_by_id', kwargs)

    def list_food_items(self, **kwargs):
        return self._call_inner_tool('list_food_items', kwargs)

    def get_nutritional_info_for_food(self, **kwargs):
        return self._call_inner_tool('get_nutritional_info_for_food', kwargs)

    def get_user_nutritional_goals(self, **kwargs):
        return self._call_inner_tool('get_user_nutritional_goals', kwargs)

    def get_daily_nutrition_summary(self, **kwargs):
        return self._call_inner_tool('get_daily_nutrition_summary', kwargs)

    def create_meal_entry(self, **kwargs):
        return self._call_inner_tool('create_meal_entry', kwargs)

    def add_item_to_meal_entry(self, **kwargs):
        return self._call_inner_tool('add_item_to_meal_entry', kwargs)

    def create_food_item(self, **kwargs):
        return self._call_inner_tool('create_food_item', kwargs)

    def edit_meal_entry(self, **kwargs):
        return self._call_inner_tool('edit_meal_entry', kwargs)

    def edit_meal_entry_item(self, **kwargs):
        return self._call_inner_tool('edit_meal_entry_item', kwargs)

    def remove_meal_entry_item(self, **kwargs):
        return self._call_inner_tool('remove_meal_entry_item', kwargs)

    def delete_meal_entry(self, **kwargs):
        return self._call_inner_tool('delete_meal_entry', kwargs)

    def update_user_dietary_goals(self, **kwargs):
        return self._call_inner_tool('update_user_dietary_goals', kwargs)

    def update_food_item(self, **kwargs):
        return self._call_inner_tool('update_food_item', kwargs)

    def duplicate_meal_entry(self, **kwargs):
        return self._call_inner_tool('duplicate_meal_entry', kwargs)

