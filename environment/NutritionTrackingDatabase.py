# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict, Any
import uuid
from typing import Optional
from typing import Dict, Any



class UserInfo(TypedDict):
    _id: str
    name: str
    age: int
    sex: str
    weight: float
    height: float
    activity_level: str

class FoodItemInfo(TypedDict):
    food_id: str
    name: str
    brand: str
    serving_size: float
    calories: float
    macronutrients: Dict[str, float]           # e.g., {"protein": x, "fat": y, "carbohydrate": z}
    micronutrients: Dict[str, float]           # e.g., {"vitamin_c": x, "iron": y, ...}

class FoodLogInfo(TypedDict):
    log_id: str
    user_id: str
    food_id: str
    date: str
    serving_size: float
    calculated_nutrients: Dict[str, float]     # e.g., {"calories": x, "protein": y, ...}

class NutritionGoalInfo(TypedDict):
    goal_id: str
    user_id: str
    date: str
    calorie_goal: float
    macronutrient_goals: Dict[str, float]      # e.g., {"protein_goal": x, "fat_goal": y, "carb_goal": z}
    micronutrient_goals: Dict[str, float]      # e.g., {"vitamin_c": x, "iron": y, ...}

class _GeneratedEnvImpl:
    def __init__(self):
        # Users: {_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}

        # FoodItems: {food_id: FoodItemInfo}
        self.food_items: Dict[str, FoodItemInfo] = {}

        # FoodLogs: {log_id: FoodLogInfo}
        self.food_logs: Dict[str, FoodLogInfo] = {}

        # NutritionGoals: {goal_id: NutritionGoalInfo}
        self.nutrition_goals: Dict[str, NutritionGoalInfo] = {}

        # Constraints:
        # - FoodLog entries must reference valid FoodItems and Users.
        # - Nutrient calculations for daily intake sum all FoodLog entries for the user and date.
        # - Remaining nutrient values are calculated as goal minus intake per nutrient for each day.
        # - NutritionGoal may vary by user and date (e.g., based on plan or adjustments).
        # - Daily summaries aggregate nutrients from FoodLog for a user and date.

    def get_user_info(self, user_id: str) -> dict:
        """
        Retrieve detailed user profile (ID, demographics, activity level, etc.) by user_id.

        Args:
            user_id (str): The unique identifier for the user.

        Returns:
            dict: 
                - On success: { "success": True, "data": UserInfo }
                - On failure: { "success": False, "error": "User not found" }

        Constraints:
            - The user_id must exist in the database.
        """
        user = self.users.get(user_id)
        if user is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user }

    def get_food_item_info(
        self,
        food_id: str = None,
        name: str = None,
        brand: str = None
    ) -> dict:
        """
        Retrieve nutritional information about a specific food item.

        Args:
            food_id (str, optional): Unique identifier for the food item.
            name (str, optional): Name of the food item (used with brand for lookup).
            brand (str, optional): Brand of the food item (used with name for lookup).

        Returns:
            dict:
                {
                    "success": True,
                    "data": FoodItemInfo
                }
                or
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - At least 'food_id' OR both 'name' and 'brand' must be provided.
            - If multiple items match name/brand, the first match is returned.

        """
        # Lookup by food_id if provided
        if food_id:
            item = self.food_items.get(food_id)
            if item is not None:
                return { "success": True, "data": item }
            else:
                return { "success": False, "error": "Food item not found for given food_id" }

        # Otherwise, require both name and brand
        if name and brand:
            for item in self.food_items.values():
                if item["name"] == name and item["brand"] == brand:
                    return { "success": True, "data": item }
            return { "success": False, "error": "Food item not found for given name and brand" }

        return { "success": False, "error": "Must provide food_id or both name and brand" }

    def list_food_logs_by_user_and_date(self, user_id: str, date: str) -> dict:
        """
        Retrieve all FoodLog entries for a specific user and date.

        Args:
            user_id (str): The user's unique identifier.
            date (str): The date to filter logs by ('YYYY-MM-DD').

        Returns:
            dict: {
                "success": True,
                "data": List[FoodLogInfo]  # List of FoodLogInfo for that user and date (empty if none)
            }
            or
            {
                "success": False,
                "error": str  # If the user does not exist
            }

        Constraints:
            - user_id must exist in the database.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        matching_logs = [
            log for log in self.food_logs.values()
            if log["user_id"] == user_id and log["date"] == date
        ]

        return {"success": True, "data": matching_logs}

    def get_nutrition_goal_by_user_and_date(self, user_id: str, date: str) -> dict:
        """
        Retrieve the nutrition goal (calories, macronutrients, micronutrients) for a specific user and date.

        Args:
            user_id (str): The unique identifier of the user.
            date (str): The target date in "YYYY-MM-DD" format.

        Returns:
            dict: 
                {
                    "success": True,
                    "data": NutritionGoalInfo  # Full goal info if found.
                }
                or
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - user_id must exist.
            - goal must exist for given user and date.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }

        for goal in self.nutrition_goals.values():
            if goal["user_id"] == user_id and goal["date"] == date:
                return { "success": True, "data": goal }

        return { "success": False, "error": "No nutrition goal set for user and date" }

    def aggregate_daily_nutrient_intake(self, user_id: str, date: str) -> dict:
        """
        Calculate total calories, macronutrients, and micronutrients consumed
        by a user on a given date by summing all FoodLog entries for that day.

        Args:
            user_id (str): The user's unique identifier.
            date (str): The date of interest (format: "YYYY-MM-DD").

        Returns:
            dict:
                {
                    "success": True,
                    "data": {
                        "calories": float,
                        "macronutrients": Dict[str, float],
                        "micronutrients": Dict[str, float]
                    }
                }
                OR
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - User must exist.
            - Zero values are returned for nutrients if no matching logs exist.
        """
        # Check user exists
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}

        # Find all matching FoodLogs
        logs = [
            log for log in self.food_logs.values()
            if log["user_id"] == user_id and log["date"] == date
        ]
    
        total_calories = 0.0
        macro_totals: Dict[str, float] = {}
        micro_totals: Dict[str, float] = {}

        for log in logs:
            # Each log has calculated_nutrients (calories, macros, micros mixed in one dict)
            nutrients = log.get("calculated_nutrients", {})
            for k, v in nutrients.items():
                if k == "calories":
                    total_calories += v
                elif k in ("protein", "fat", "carbohydrate"):
                    macro_totals[k] = macro_totals.get(k, 0.0) + v
                else:
                    micro_totals[k] = micro_totals.get(k, 0.0) + v

        # Ensure all macros (protein, fat, carbohydrate) present
        for macro in ("protein", "fat", "carbohydrate"):
            if macro not in macro_totals:
                macro_totals[macro] = 0.0

        result = {
            "calories": total_calories,
            "macronutrients": macro_totals,
            "micronutrients": micro_totals
        }
        return {"success": True, "data": result}

    def calculate_remaining_nutrients(self, user_id: str, date: str) -> dict:
        """
        For a given user and date, calculate the remaining nutrients as (goal - intake) for calories,
        all macronutrients, and all micronutrients.

        Args:
            user_id (str): ID of the user.
            date (str): Date string for which calculation is performed.

        Returns:
            dict: {
                "success": True,
                "data": { <nutrient>: remaining_amount (float), ... }
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - User must exist.
            - There must be a NutritionGoal for the user and date.
            - Intake per nutrient is summed from all FoodLogs for the user/date (missing means zero).
            - Remaining = goal - intake for every goal-tracked nutrient (calories, macros, micros).
        """
        # Check if user exists
        if user_id not in self.users:
            return { "success": False, "error": "User does not exist" }

        # Find the relevant goal for this user and date
        goal_info = None
        for ng in self.nutrition_goals.values():
            if ng["user_id"] == user_id and ng["date"] == date:
                goal_info = ng
                break

        if not goal_info:
            return { "success": False, "error": "Nutrition goal not found for user and date" }

        # Aggregate intake from all relevant food logs
        intake = {}
        # Calories
        intake["calories"] = 0.0
        # Macros: get keys from goal (if any)
        macro_keys = list(goal_info.get("macronutrient_goals", {}).keys())
        for macro in macro_keys:
            intake[macro.replace("_goal", "")] = 0.0  # Keys in logs are e.g., "protein"
        # Micros: get keys from goal (if any)
        micro_keys = list(goal_info.get("micronutrient_goals", {}).keys())
        for micro in micro_keys:
            intake[micro] = 0.0

        # Sum from all food logs for user/date
        for log in self.food_logs.values():
            if log["user_id"] == user_id and log["date"] == date:
                nutrients = log.get("calculated_nutrients", {})
                # Calories
                intake["calories"] += nutrients.get("calories", 0.0)
                # Macros
                for macro in macro_keys:
                    nutrient_name = macro.replace("_goal", "")  # E.g. protein_goal -> protein
                    intake[nutrient_name] += nutrients.get(nutrient_name, 0.0)
                # Micros
                for micro in micro_keys:
                    intake[micro] += nutrients.get(micro, 0.0)

        # Compute remaining: goal - intake for each tracked nutrient
        result = {}

        # Calories
        result["calories"] = goal_info.get("calorie_goal", 0.0) - intake["calories"]
        # Macros
        for macro in macro_keys:
            macro_short = macro.replace("_goal", "")
            goal_amount = goal_info["macronutrient_goals"].get(macro, 0.0)
            result[macro_short] = goal_amount - intake[macro_short]
        # Micros
        for micro in micro_keys:
            goal_amount = goal_info["micronutrient_goals"].get(micro, 0.0)
            result[micro] = goal_amount - intake[micro]

        return { "success": True, "data": result }

    def get_daily_summary(self, user_id: str, date: str) -> dict:
        """
        Produce a formatted summary for a given user and date, showing intake and remaining for each tracked nutrient.

        Args:
            user_id (str): The ID of the user.
            date (str): The date to summarize (format: YYYY-MM-DD).

        Returns:
            dict:
                success (bool): Whether the operation succeeded.
                data (dict): If successful, contains user_id, date, and a nutrients mapping (nutrient_name -> dict with 'intake', 'goal', 'remaining').
                error (str): If failed, reason for failure.

        Constraints:
            - The user must exist.
            - NutritionGoal must be defined for the user and date.
        """
        if user_id not in self.users:
            return {"success": False, "error": "User not found"}
    
        # Find the nutrition goal for this user and date
        goal: NutritionGoalInfo = None
        for ng in self.nutrition_goals.values():
            if ng["user_id"] == user_id and ng["date"] == date:
                goal = ng
                break
        if not goal:
            return {"success": False, "error": "Nutrition goal for user and date not found"}

        # Aggregate FoodLogs for the user and date
        intake_totals = {}  # nutrient_name -> sum value
        for flog in self.food_logs.values():
            if flog["user_id"] == user_id and flog["date"] == date:
                for nutrient, value in flog["calculated_nutrients"].items():
                    intake_totals[nutrient] = intake_totals.get(nutrient, 0.0) + value

        # Collect all tracked nutrients (from both intake and goal)
        tracked_nutrients = set(intake_totals.keys())
        # Add known macro/micronutrient goals (suffix: _goal for macros, raw for calories)
        # Add all macronutrient/micronutrient goals
        goal_names_map = {}  # nutrient_name -> goal_value

        # Always add "calories"
        if "calorie_goal" in goal:
            goal_names_map["calories"] = goal["calorie_goal"]

        # Macronutrients (e.g., "protein_goal" -> "protein")
        for macro_goal, value in goal.get("macronutrient_goals", {}).items():
            if macro_goal.endswith("_goal"):
                n = macro_goal[:-5]  # Remove "_goal"
            else:
                n = macro_goal
            goal_names_map[n] = value
            tracked_nutrients.add(n)
        # Micronutrients
        for micro, value in goal.get("micronutrient_goals", {}).items():
            goal_names_map[micro] = value
            tracked_nutrients.add(micro)
        # Add any nutrients from intake absent in goal
        for nutrient in intake_totals:
            tracked_nutrients.add(nutrient)

        nutrient_summary = {}
        for nutrient in tracked_nutrients:
            intake = intake_totals.get(nutrient, 0.0)
            goal_val = goal_names_map.get(nutrient, None)
            # if goal is missing, remaining is None
            if goal_val is not None:
                remaining = goal_val - intake
            else:
                remaining = None
            nutrient_summary[nutrient] = {
                "intake": intake,
                "goal": goal_val,
                "remaining": remaining
            }

        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "date": date,
                "nutrients": nutrient_summary
            }
        }

    def list_all_users(self) -> dict:
        """
        Retrieve a list of all users in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[UserInfo],   # List of all user information dicts (possibly empty)
            }

        Constraints:
            - This operation simply aggregates all UserInfo records with no permission checks.
            - No error is returned if there are no users; data will be the empty list.
        """
        return {
            "success": True,
            "data": list(self.users.values())
        }

    def list_all_food_items(self) -> dict:
        """
        Retrieve all available food items and their nutrition info.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[FoodItemInfo]  # List of all food items' info (may be empty if no items exist)
            }
        """
        all_food_items = list(self.food_items.values())
        return {
            "success": True,
            "data": all_food_items
        }


    def add_food_log(
        self,
        user_id: str,
        food_id: str,
        date: str,
        serving_size: float,
        log_id: Optional[str] = None
    ) -> dict:
        """
        Create a new FoodLog entry for a user referencing a valid FoodItem.

        Args:
            user_id (str): ID of the user who consumed the food.
            food_id (str): ID of the food item.
            date (str): Consumption date ('YYYY-MM-DD').
            serving_size (float): Amount of food consumed (in food item's units).
            log_id (Optional[str]): Optionally specify log ID, else auto-generate.

        Returns:
            dict:
                On success: {
                    "success": True,
                    "message": "Food log added",
                    "log_id": <new_log_id>
                }
                On error: {
                    "success": False,
                    "error": <reason>
                }

        Constraints:
            - user_id must reference an existing user.
            - food_id must reference an existing food item.
            - serving_size must be positive.
            - Each log_id must be unique.
        """
        # Constraint checks
        if user_id not in self.users:
            return {"success": False, "error": "User does not exist"}
        if food_id not in self.food_items:
            return {"success": False, "error": "Food item does not exist"}
        if serving_size <= 0:
            return {"success": False, "error": "Serving size must be positive"}

        if log_id is None:
            # Generate a unique log_id
            log_id = str(uuid.uuid4())
        elif log_id in self.food_logs:
            return {"success": False, "error": "Log ID already exists"}

        food_item = self.food_items[food_id]
        base_serving = food_item["serving_size"]
        scaling = serving_size / base_serving if base_serving > 0 else 1.0

        # Calculate scaled nutrients
        calculated_nutrients = {}
        # Calories
        calculated_nutrients["calories"] = food_item.get("calories", 0.0) * scaling
        # Macronutrients
        for key, value in food_item.get("macronutrients", {}).items():
            calculated_nutrients[key] = value * scaling
        # Micronutrients
        for key, value in food_item.get("micronutrients", {}).items():
            calculated_nutrients[key] = value * scaling

        food_log_info = {
            "log_id": log_id,
            "user_id": user_id,
            "food_id": food_id,
            "date": date,
            "serving_size": serving_size,
            "calculated_nutrients": calculated_nutrients
        }

        self.food_logs[log_id] = food_log_info

        return {"success": True, "message": "Food log added", "log_id": log_id}

    def update_food_log(self, log_id: str, food_id: str = None, serving_size: float = None) -> dict:
        """
        Edit the serving size and/or food item in an existing FoodLog entry.

        Args:
            log_id (str): The identifier of the FoodLog entry to update.
            food_id (str, optional): The new food_id to use (must exist in food_items).
            serving_size (float, optional): The new serving size to use (must be > 0).

        Returns:
            dict: On success: { "success": True, "message": "FoodLog updated successfully" }
                  On failure: { "success": False, "error": error_message }

        Constraints:
            - FoodLog entry must exist.
            - If food_id is provided, it must exist in food_items.
            - If serving_size is provided, it must be > 0.
            - At least one of food_id or serving_size must be provided.
            - Calculated nutrients must be updated per new food and serving size.
        """
        # Check for existence of FoodLog
        if log_id not in self.food_logs:
            return { "success": False, "error": "FoodLog entry does not exist" }

        food_log = self.food_logs[log_id]

        # Determine if changes are provided
        if food_id is None and serving_size is None:
            return { "success": False, "error": "No update parameters provided" }

        # Validate and apply food_id update
        updated_food_id = food_log["food_id"]
        if food_id is not None:
            if food_id not in self.food_items:
                return { "success": False, "error": "Provided food_id does not exist" }
            updated_food_id = food_id

        # Validate and apply serving_size update
        updated_serving_size = food_log["serving_size"]
        if serving_size is not None:
            if serving_size <= 0:
                return { "success": False, "error": "Serving size must be positive" }
            updated_serving_size = serving_size

        # Get reference food item
        food_item = self.food_items[updated_food_id]
        base_serving = food_item["serving_size"]
        multiplier = updated_serving_size / base_serving if base_serving > 0 else 0

        # Recalculate nutrients (calories, macronutrients, micronutrients)
        calculated_nutrients = {}
        # Calories
        calculated_nutrients["calories"] = food_item["calories"] * multiplier
        # Macronutrients
        for macro, val in food_item["macronutrients"].items():
            calculated_nutrients[macro] = val * multiplier
        # Micronutrients
        for micro, val in food_item["micronutrients"].items():
            calculated_nutrients[micro] = val * multiplier

        # Update log fields
        food_log["food_id"] = updated_food_id
        food_log["serving_size"] = updated_serving_size
        food_log["calculated_nutrients"] = calculated_nutrients

        return { "success": True, "message": "FoodLog updated successfully" }

    def delete_food_log(self, log_id: str) -> dict:
        """
        Remove a FoodLog entry from the database.

        Args:
            log_id (str): The unique identifier of the FoodLog entry to delete.

        Returns:
            dict: {
                "success": True,
                "message": "FoodLog <log_id> deleted successfully."
            }
            or
            {
                "success": False,
                "error": "FoodLog entry not found."
            }

        Constraints:
            - FoodLog entry with the given log_id must exist.
        """
        if log_id not in self.food_logs:
            return { "success": False, "error": "FoodLog entry not found." }

        del self.food_logs[log_id]
        return { "success": True, "message": f"FoodLog {log_id} deleted successfully." }


    def add_nutrition_goal(
        self,
        user_id: str,
        date: str,
        calorie_goal: float,
        macronutrient_goals: Dict[str, float],
        micronutrient_goals: Dict[str, float],
    ) -> dict:
        """
        Define or update a NutritionGoal for a user and date.

        Args:
            user_id (str): User's unique identifier. Must exist.
            date (str): Date string (e.g., 'YYYY-MM-DD').
            calorie_goal (float): Total calories goal.
            macronutrient_goals (Dict[str, float]): Goals for macros (e.g., {'protein_goal': X, ...}).
            micronutrient_goals (Dict[str, float]): Goals for micros (vitamins, minerals).

        Returns:
            dict, on success: {"success": True, "message": "..."}
                  on failure: {"success": False, "error": "..."}
        Constraints:
            - user_id must reference an existing user.
            - For a given (user_id, date), at most one NutritionGoal exists.
        """
        # Verify the user exists
        if user_id not in self.users:
            return {"success": False, "error": f"User with id {user_id} does not exist"}

        # Find if a NutritionGoal for (user_id, date) already exists
        current_goal_id = None
        for goal_id, goal in self.nutrition_goals.items():
            if goal["user_id"] == user_id and goal["date"] == date:
                current_goal_id = goal_id
                break

        # Preparing the goal structure
        new_goal_info = {
            "goal_id": current_goal_id if current_goal_id is not None else str(uuid.uuid4()),
            "user_id": user_id,
            "date": date,
            "calorie_goal": calorie_goal,
            "macronutrient_goals": macronutrient_goals,
            "micronutrient_goals": micronutrient_goals,
        }

        if current_goal_id is not None:
            # Update existing goal
            self.nutrition_goals[current_goal_id] = new_goal_info
            action = "updated"
        else:
            # Add new goal
            self.nutrition_goals[new_goal_info["goal_id"]] = new_goal_info
            action = "added"

        return {
            "success": True,
            "message": f"Nutrition goal for user {user_id} on {date} {action}."
        }

    def update_nutrition_goal(
        self,
        goal_id: str,
        calorie_goal: float = None,
        macronutrient_goals: dict = None,
        micronutrient_goals: dict = None
    ) -> dict:
        """
        Modify an existing day's NutritionGoal (calorie/macros/micros).
    
        Args:
            goal_id (str): The unique ID of the NutritionGoal to update.
            calorie_goal (float, optional): New calorie goal.
            macronutrient_goals (dict, optional): New dict of macro goals, ex: {"protein_goal": x, ...}
            micronutrient_goals (dict, optional): New dict of micro goals, ex: {"vitamin_c": x, ...}
        
        Returns:
            dict: {
                "success": True,
                "message": "NutritionGoal <goal_id> updated."
            }
            or
            {
                "success": False,
                "error": error_message
            }

        Constraints:
            - NutritionGoal (goal_id) must exist.
            - Only valid types are accepted for update fields.
        """
        # Check that NutritionGoal exists
        if goal_id not in self.nutrition_goals:
            return {"success": False, "error": f"NutritionGoal {goal_id} does not exist."}
    
        ng = self.nutrition_goals[goal_id]

        updated = False
    
        if calorie_goal is not None:
            if not isinstance(calorie_goal, (int, float)):
                return {"success": False, "error": "calorie_goal must be a number"}
            ng["calorie_goal"] = float(calorie_goal)
            updated = True
    
        if macronutrient_goals is not None:
            if not isinstance(macronutrient_goals, dict) or \
               not all(isinstance(k, str) and isinstance(v, (int, float)) for k, v in macronutrient_goals.items()):
                return {"success": False, "error": "macronutrient_goals must be a dict of str: float"}
            ng["macronutrient_goals"] = {k: float(v) for k, v in macronutrient_goals.items()}
            updated = True
    
        if micronutrient_goals is not None:
            if not isinstance(micronutrient_goals, dict) or \
               not all(isinstance(k, str) and isinstance(v, (int, float)) for k, v in micronutrient_goals.items()):
                return {"success": False, "error": "micronutrient_goals must be a dict of str: float"}
            ng["micronutrient_goals"] = {k: float(v) for k, v in micronutrient_goals.items()}
            updated = True

        if not updated:
            return {"success": False, "error": "No valid update fields provided."}

        return {"success": True, "message": f"NutritionGoal {goal_id} updated."}

    def delete_nutrition_goal(self, user_id: str, date: str) -> dict:
        """
        Remove (delete) a NutritionGoal entry for a given user and date.

        Args:
            user_id (str): The user identifier.
            date (str): The calendar date string (e.g., '2024-06-30').

        Returns:
            dict:
                - On success:
                    { "success": True, "message": "Nutrition goal deleted for user {user_id} on {date}" }
                - If no matching goal:
                    { "success": False, "error": "No nutrition goal found for user {user_id} on {date}" }
                - If input is missing:
                    { "success": False, "error": "user_id and date must be provided" }

        Constraints:
            - Only allows deletion of goals tied to a valid user/date.
            - If multiple goals exist for the same user/date, delete all.
        """
        if not user_id or not date:
            return { "success": False, "error": "user_id and date must be provided" }

        to_delete = [goal_id for goal_id, info in self.nutrition_goals.items()
                     if info["user_id"] == user_id and info["date"] == date]
        if not to_delete:
            return { "success": False, "error": f"No nutrition goal found for user {user_id} on {date}" }

        for goal_id in to_delete:
            del self.nutrition_goals[goal_id]

        return { "success": True, "message": f"Nutrition goal deleted for user {user_id} on {date}" }

    def add_food_item(
        self,
        food_id: str,
        name: str,
        brand: str,
        serving_size: float,
        calories: float,
        macronutrients: Dict[str, float],
        micronutrients: Dict[str, float]
    ) -> dict:
        """
        Create a new FoodItem (with nutrient info) for logging.

        Args:
            food_id (str): Unique identifier for the food item.
            name (str): Name of the food.
            brand (str): Brand of the food.
            serving_size (float): Serving size of the food item.
            calories (float): Calories per serving.
            macronutrients (dict): Macronutrient values per serving (protein, fat, carbohydrate keys recommended).
            micronutrients (dict): Micronutrient values per serving.

        Returns:
            dict:
                Success: {"success": True, "message": "Food item '<name>' added successfully."}
                Failure: {"success": False, "error": "<reason>"}

        Constraints:
            - food_id must be unique.
            - All arguments must be provided and of the correct type.
            - Macronutrients should contain keys: protein, fat, carbohydrate (set to 0.0 if missing).
        """
        # Uniqueness check
        if food_id in self.food_items:
            return {"success": False, "error": "Food item with this food_id already exists."}

        # Field/type checks
        if not isinstance(food_id, str) or not food_id.strip():
            return {"success": False, "error": "Field 'food_id' is missing or invalid."}
        if not isinstance(name, str) or not name.strip():
            return {"success": False, "error": "Field 'name' is missing or invalid."}
        if not isinstance(brand, str):
            return {"success": False, "error": "Field 'brand' is missing or invalid."}
        if not (isinstance(serving_size, (int, float)) and serving_size > 0):
            return {"success": False, "error": "Field 'serving_size' is missing or invalid."}
        if not (isinstance(calories, (int, float)) and calories >= 0):
            return {"success": False, "error": "Field 'calories' is missing or invalid."}
        if not isinstance(macronutrients, dict):
            return {"success": False, "error": "Field 'macronutrients' is missing or invalid."}
        if not isinstance(micronutrients, dict):
            return {"success": False, "error": "Field 'micronutrients' is missing or invalid."}

        processed_macros = {}
        for macro in ["protein", "fat", "carbohydrate"]:
            val = macronutrients.get(macro, 0.0)
            if not isinstance(val, (int, float)):
                return {"success": False, "error": f"Macronutrient '{macro}' must be a number."}
            processed_macros[macro] = float(val)
        # Include any extra macros
        for macro, val in macronutrients.items():
            if macro not in processed_macros:
                if not isinstance(val, (int, float)):
                    return {"success": False, "error": f"Macronutrient '{macro}' must be a number."}
                processed_macros[macro] = float(val)

        # Ensure micronutrient values are numbers
        processed_micros = {}
        for micro, val in micronutrients.items():
            if not isinstance(val, (int, float)):
                return {"success": False, "error": f"Micronutrient '{micro}' must be a number."}
            processed_micros[micro] = float(val)

        # Construct the FoodItemInfo dict
        food_info = {
            "food_id": food_id,
            "name": name,
            "brand": brand,
            "serving_size": float(serving_size),
            "calories": float(calories),
            "macronutrients": processed_macros,
            "micronutrients": processed_micros,
        }

        self.food_items[food_id] = food_info

        return {"success": True, "message": f"Food item '{name}' added successfully."}

    def update_food_item(
        self,
        food_id: str,
        name: str = None,
        brand: str = None,
        serving_size: float = None,
        calories: float = None,
        macronutrients: Dict[str, float] = None,
        micronutrients: Dict[str, float] = None
    ) -> dict:
        """
        Edit nutritional info for an existing FoodItem, allowing partial updates.

        Args:
            food_id (str): The unique ID of the food item to update.
            name (str, optional): New name.
            brand (str, optional): New brand.
            serving_size (float, optional): New serving size. Must be positive if provided.
            calories (float, optional): New calorie value. Must be >= 0 if provided.
            macronutrients (Dict[str, float], optional): New macro dict. All values must be >= 0.
            micronutrients (Dict[str, float], optional): New micro dict. All values must be >= 0.

        Returns:
            dict: {
                "success": True,
                "message": "Food item updated."
            }
            or {
                "success": False,
                "error": str
            }
        """
        # Check FoodItem existence
        if food_id not in self.food_items:
            return { "success": False, "error": "FoodItem not found." }
    
        food = self.food_items[food_id]

        # Validate and update fields if provided
        if name is not None:
            food["name"] = name
        if brand is not None:
            food["brand"] = brand

        if serving_size is not None:
            if not isinstance(serving_size, (int, float)) or serving_size <= 0:
                return { "success": False, "error": "serving_size must be a positive number." }
            food["serving_size"] = serving_size

        if calories is not None:
            if not isinstance(calories, (int, float)) or calories < 0:
                return { "success": False, "error": "calories must be a non-negative number." }
            food["calories"] = calories

        if macronutrients is not None:
            if not isinstance(macronutrients, dict):
                return { "success": False, "error": "macronutrients must be a dictionary." }
            for k, v in macronutrients.items():
                if not isinstance(v, (int, float)) or v < 0:
                    return { "success": False, "error": f"Macronutrient '{k}' value must be non-negative." }
            food["macronutrients"] = macronutrients

        if micronutrients is not None:
            if not isinstance(micronutrients, dict):
                return { "success": False, "error": "micronutrients must be a dictionary." }
            for k, v in micronutrients.items():
                if not isinstance(v, (int, float)) or v < 0:
                    return { "success": False, "error": f"Micronutrient '{k}' value must be non-negative." }
            food["micronutrients"] = micronutrients

        # Save back to the dict (not strictly necessary since dicts are by reference)
        self.food_items[food_id] = food

        return { "success": True, "message": "Food item updated." }

    def delete_food_item(self, food_id: str) -> dict:
        """
        Remove a FoodItem from the reference database.

        Args:
            food_id (str): The unique identifier of the FoodItem to be deleted.

        Returns:
            dict:
                - If success:
                    {"success": True, "message": "FoodItem <food_id> deleted."}
                - If food_id does not exist:
                    {"success": False, "error": "FoodItem not found."}
                - If FoodItem is referenced by any FoodLog:
                    {"success": False, "error": "FoodItem is referenced by one or more FoodLogs and cannot be deleted."}

        Constraints:
            - Cannot delete FoodItem if it is referenced by existing FoodLogs.
        """
        if food_id not in self.food_items:
            return {"success": False, "error": "FoodItem not found."}

        # Check if any FoodLog references this FoodItem
        referenced = any(log["food_id"] == food_id for log in self.food_logs.values())
        if referenced:
            return {
                "success": False,
                "error": "FoodItem is referenced by one or more FoodLogs and cannot be deleted."
            }
    
        del self.food_items[food_id]
        return {"success": True, "message": f"FoodItem {food_id} deleted."}


class NutritionTrackingDatabase(BaseEnv):
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

    def get_user_info(self, **kwargs):
        return self._call_inner_tool('get_user_info', kwargs)

    def get_food_item_info(self, **kwargs):
        return self._call_inner_tool('get_food_item_info', kwargs)

    def list_food_logs_by_user_and_date(self, **kwargs):
        return self._call_inner_tool('list_food_logs_by_user_and_date', kwargs)

    def get_nutrition_goal_by_user_and_date(self, **kwargs):
        return self._call_inner_tool('get_nutrition_goal_by_user_and_date', kwargs)

    def aggregate_daily_nutrient_intake(self, **kwargs):
        return self._call_inner_tool('aggregate_daily_nutrient_intake', kwargs)

    def calculate_remaining_nutrients(self, **kwargs):
        return self._call_inner_tool('calculate_remaining_nutrients', kwargs)

    def get_daily_summary(self, **kwargs):
        return self._call_inner_tool('get_daily_summary', kwargs)

    def list_all_users(self, **kwargs):
        return self._call_inner_tool('list_all_users', kwargs)

    def list_all_food_items(self, **kwargs):
        return self._call_inner_tool('list_all_food_items', kwargs)

    def add_food_log(self, **kwargs):
        return self._call_inner_tool('add_food_log', kwargs)

    def update_food_log(self, **kwargs):
        return self._call_inner_tool('update_food_log', kwargs)

    def delete_food_log(self, **kwargs):
        return self._call_inner_tool('delete_food_log', kwargs)

    def add_nutrition_goal(self, **kwargs):
        return self._call_inner_tool('add_nutrition_goal', kwargs)

    def update_nutrition_goal(self, **kwargs):
        return self._call_inner_tool('update_nutrition_goal', kwargs)

    def delete_nutrition_goal(self, **kwargs):
        return self._call_inner_tool('delete_nutrition_goal', kwargs)

    def add_food_item(self, **kwargs):
        return self._call_inner_tool('add_food_item', kwargs)

    def update_food_item(self, **kwargs):
        return self._call_inner_tool('update_food_item', kwargs)

    def delete_food_item(self, **kwargs):
        return self._call_inner_tool('delete_food_item', kwargs)

