# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



class IngredientInfo(TypedDict):
    ingredient_name: str
    quantity: float
    unit: str

class RecipeInfo(TypedDict):
    recipe_id: str
    title: str
    ingredient_list: List[IngredientInfo]
    instructions: str
    cuisine: str
    difficulty_level: str
    preparation_time: float
    tags: List[str]
    date_created: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment for managing collections of cooking recipes.
        """

        # Recipes: {recipe_id: RecipeInfo}
        self.recipes: Dict[str, RecipeInfo] = {}

        # Constraints:
        # - recipe_id must be unique across all recipes
        # - Ingredient lists must be non-empty for valid recipes
        # - Recipes must have at least a title and instructions to be valid

    def get_recipe_by_id(self, recipe_id: str) -> dict:
        """
        Retrieve the complete details of a recipe given its recipe_id.
    
        Args:
            recipe_id (str): The unique identifier for the recipe.
    
        Returns:
            dict: {
                "success": True,
                "data": RecipeInfo  # Complete details of the recipe
            }
            OR
            {
                "success": False,
                "error": str  # Reason for failure (e.g., recipe_id not found)
            }
    
        Constraints:
            - recipe_id must exist in the system.
        """
        recipe = self.recipes.get(recipe_id)
        if recipe is None:
            return {"success": False, "error": "Recipe ID not found"}
        return {"success": True, "data": recipe}

    def list_all_recipes(self) -> dict:
        """
        Retrieve a list of all recipes present in the system.

        Args:
            None

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[RecipeInfo],  # Possibly empty if no recipes exist
                }
        """
        all_recipes = list(self.recipes.values())
        return {
            "success": True,
            "data": all_recipes
        }

    def search_recipes_by_title(self, title_query: str) -> dict:
        """
        Search and retrieve all recipes whose title contains the given string (case-insensitive).
    
        Args:
            title_query (str): Full or partial title to search for.

        Returns:
            dict: {
                "success": True,
                "data": List[RecipeInfo]  # List of matching recipes, may be empty
            }

        Constraints:
            - Only retrieves recipes where `title_query` is a substring (case-insensitive) of recipe's title.
        """
        # Prepare for case-insensitive matching
        q = title_query.lower()
        results = [
            recipe for recipe in self.recipes.values()
            if q in recipe['title'].lower()
        ]
        return { "success": True, "data": results }

    def filter_recipes_by_cuisine(self, cuisine: str) -> dict:
        """
        Retrieve all recipes with the specified cuisine.

        Args:
            cuisine (str): The cuisine type to filter recipes by.

        Returns:
            dict: {
                "success": True,
                "data": List[RecipeInfo]  # all recipes whose cuisine matches the argument (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # if the cuisine argument is missing or invalid
            }

        Constraints:
            - cuisine must be provided (non-empty string).
        """
        if not isinstance(cuisine, str) or not cuisine.strip():
            return {"success": False, "error": "Cuisine must be a non-empty string"}

        filtered = [
            recipe for recipe in self.recipes.values()
            if recipe.get("cuisine", "").lower() == cuisine.lower()
        ]
        return {"success": True, "data": filtered}

    def filter_recipes_by_tag(self, tag: str) -> dict:
        """
        Retrieve all recipes that include a specific tag.

        Args:
            tag (str): The tag to filter recipes by.

        Returns:
            dict: {
                "success": True,
                "data": List[RecipeInfo]  # List of matching recipes (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Description of error, e.g., invalid tag
            }

        Constraints:
            - Tag should be a non-empty string.
        """
        if not isinstance(tag, str) or not tag.strip():
            return {"success": False, "error": "Tag must be a non-empty string"}

        filtered_recipes = [
            recipe_info
            for recipe_info in self.recipes.values()
            if tag in recipe_info.get("tags", [])
        ]

        return {"success": True, "data": filtered_recipes}

    def filter_recipes_by_difficulty(self, difficulty_level: str) -> dict:
        """
        Retrieve all recipes with the specified difficulty level.

        Args:
            difficulty_level (str): The difficulty level to filter recipes by.

        Returns:
            dict:
                - On success: {
                    "success": True,
                    "data": List[RecipeInfo]  # List of matching recipes (may be empty)
                }
                - On error: {
                    "success": False,
                    "error": str
                }

        Constraints:
            - No specific constraint on allowed difficulty levels.
            - Returns empty list if no matching recipes.
        """
        if not isinstance(difficulty_level, str) or not difficulty_level:
            return {"success": False, "error": "Difficulty level must be a non-empty string"}
    
        result = [
            recipe for recipe in self.recipes.values()
            if recipe.get("difficulty_level") == difficulty_level
        ]

        return {"success": True, "data": result}

    def filter_recipes_by_prep_time(self, min_time: float, max_time: float) -> dict:
        """
        Retrieve all recipes whose preparation time falls within the inclusive range [min_time, max_time].

        Args:
            min_time (float): The minimum preparation time (inclusive).
            max_time (float): The maximum preparation time (inclusive).

        Returns:
            dict:
                - On success:
                    {"success": True, "data": List[RecipeInfo]}
                - On error:
                    {"success": False, "error": str}
    
        Constraints:
            - min_time must not be greater than max_time.
        """
        if min_time > max_time:
            return {
                "success": False,
                "error": "min_time must be less than or equal to max_time"
            }

        results = [
            recipe
            for recipe in self.recipes.values()
            if min_time <= recipe["preparation_time"] <= max_time
        ]

        return {"success": True, "data": results}

    def get_ingredient_list_for_recipe(self, recipe_id: str) -> dict:
        """
        Retrieve the full list of ingredients for a specific recipe.

        Args:
            recipe_id (str): The unique identifier of the recipe.

        Returns:
            dict: 
                On success:
                    {"success": True, "data": List[IngredientInfo]}
                On error (e.g. recipe not found): 
                    {"success": False, "error": str}
        Constraints:
            - recipe_id must exist in the system.
        """
        recipe = self.recipes.get(recipe_id)
        if not recipe:
            return {"success": False, "error": "Recipe not found"}
        return {"success": True, "data": recipe.get("ingredient_list", [])}

    def add_recipe(self,
                   recipe_id: str,
                   title: str,
                   ingredient_list: list,
                   instructions: str,
                   cuisine: str,
                   difficulty_level: str,
                   preparation_time: float,
                   tags: list,
                   date_created: str
                  ) -> dict:
        """
        Add a new recipe to the system, enforcing all constraints:
          - recipe_id must be unique
          - ingredient_list must be non-empty
          - title and instructions must be provided and non-empty

        Args:
            recipe_id (str): Unique identifier for the recipe.
            title (str): The title/name of the recipe.
            ingredient_list (list[IngredientInfo]): List of ingredient dicts.
            instructions (str): Cooking instructions.
            cuisine (str): Cuisine type.
            difficulty_level (str): Difficulty label.
            preparation_time (float): Preparation time in minutes.
            tags (list[str]): Associated tags.
            date_created (str): Creation date string.

        Returns:
            dict: { "success": True, "message": str }
                  or
                  { "success": False, "error": str }
        """
        # Check unique recipe_id
        if recipe_id in self.recipes:
            return {"success": False, "error": "recipe_id already exists"}

        # title and instructions must be non-empty
        if not isinstance(title, str) or not title.strip():
            return {"success": False, "error": "title is required and cannot be empty"}
        if not isinstance(instructions, str) or not instructions.strip():
            return {"success": False, "error": "instructions are required and cannot be empty"}

        # ingredient_list must be non-empty
        if not isinstance(ingredient_list, list) or len(ingredient_list) == 0:
            return {"success": False, "error": "ingredient_list must be a non-empty list"}

        # Optionally: validate that each ingredient has the correct structure
        required_ing_fields = {"ingredient_name", "quantity", "unit"}
        for idx, ing in enumerate(ingredient_list):
            if not isinstance(ing, dict) or not required_ing_fields.issubset(ing.keys()):
                return {"success": False, "error": f"ingredient at position {idx} missing required fields"}

        # Build and store the RecipeInfo
        recipe_info = {
            "recipe_id": recipe_id,
            "title": title,
            "ingredient_list": ingredient_list,
            "instructions": instructions,
            "cuisine": cuisine,
            "difficulty_level": difficulty_level,
            "preparation_time": preparation_time,
            "tags": tags,
            "date_created": date_created
        }
        self.recipes[recipe_id] = recipe_info

        return {"success": True, "message": f"Recipe {recipe_id} added successfully"}

    def edit_recipe(
        self,
        recipe_id: str,
        title: str = None,
        ingredient_list: list = None,
        instructions: str = None,
        cuisine: str = None,
        difficulty_level: str = None,
        preparation_time: float = None,
        tags: list = None,
    ) -> dict:
        """
        Update details of an existing recipe, checking all constraints.
    
        Args:
            recipe_id (str): ID of the recipe to update.
            title (str, optional): New title. Leave as None to not change.
            ingredient_list (list[IngredientInfo], optional): New ingredient list. Leave as None to not change.
            instructions (str, optional): New procedural instructions. Leave as None to not change.
            cuisine (str, optional): New cuisine label. Leave as None to not change.
            difficulty_level (str, optional): New difficulty label. Leave as None to not change.
            preparation_time (float, optional): New prep time. Leave as None to not change.
            tags (list[str], optional): New list of tags. Leave as None to not change.

        Returns:
            dict: 
              Success: {"success": True, "message": "Recipe <recipe_id> updated successfully."}
              Failure: {"success": False, "error": "reason"}
          
        Constraints:
            - Recipe must exist.
            - Resulting recipe must have non-empty title, instructions, ingredient_list.
        """
        if recipe_id not in self.recipes:
            return {"success": False, "error": "Recipe not found."}
    
        recipe = self.recipes[recipe_id].copy()
    
        # Update values if provided
        if title is not None:
            recipe['title'] = title
        if ingredient_list is not None:
            recipe['ingredient_list'] = ingredient_list
        if instructions is not None:
            recipe['instructions'] = instructions
        if cuisine is not None:
            recipe['cuisine'] = cuisine
        if difficulty_level is not None:
            recipe['difficulty_level'] = difficulty_level
        if preparation_time is not None:
            recipe['preparation_time'] = preparation_time
        if tags is not None:
            recipe['tags'] = tags

        # Constraints check
        if not recipe.get('title') or not isinstance(recipe['title'], str) or not recipe['title'].strip():
            return {"success": False, "error": "Recipe must have a non-empty title."}
        if not recipe.get('instructions') or not isinstance(recipe['instructions'], str) or not recipe['instructions'].strip():
            return {"success": False, "error": "Recipe must have non-empty instructions."}
        if not recipe.get('ingredient_list') or not isinstance(recipe['ingredient_list'], list) or len(recipe['ingredient_list']) == 0:
            return {"success": False, "error": "Recipe must have a non-empty ingredient list."}
    
        # Basic validation for ingredient_list structure if updated
        if ingredient_list is not None:
            for ing in ingredient_list:
                if (
                    not isinstance(ing, dict)
                    or 'ingredient_name' not in ing
                    or 'quantity' not in ing
                    or 'unit' not in ing
                    or not isinstance(ing['ingredient_name'], str)
                ):
                    return {"success": False, "error": "Invalid ingredient in ingredient_list."}
    
        # If all checks passed, commit the update
        self.recipes[recipe_id] = recipe
        return {"success": True, "message": f"Recipe {recipe_id} updated successfully."}

    def delete_recipe(self, recipe_id: str) -> dict:
        """
        Remove a recipe from the system by its recipe_id.

        Args:
            recipe_id (str): Unique identifier of the recipe to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Recipe <recipe_id> deleted."
            }
            or
            {
                "success": False,
                "error": "Recipe with ID <recipe_id> does not exist."
            }

        Constraints:
            - recipe_id must exist in the system.
        """
        if recipe_id not in self.recipes:
            return {
                "success": False,
                "error": f"Recipe with ID {recipe_id} does not exist."
            }
        del self.recipes[recipe_id]
        return {
            "success": True,
            "message": f"Recipe {recipe_id} deleted."
        }

    def add_ingredient_to_recipe(
        self,
        recipe_id: str,
        ingredient_name: str,
        quantity: float,
        unit: str
    ) -> dict:
        """
        Adds a new ingredient to the ingredient list of the specified recipe.

        Args:
            recipe_id (str): The unique ID of the recipe to modify.
            ingredient_name (str): The name of the ingredient to add.
            quantity (float): The amount of the ingredient (should be positive).
            unit (str): The measurement unit for the ingredient.

        Returns:
            dict: 
                { "success": True, "message": "Ingredient added to recipe <id>." }
              or
                { "success": False, "error": <reason> }
        Constraints:
            - Recipe must exist.
            - Ingredient name and unit must not be empty.
            - Quantity should be positive.
            - Ingredient must not already exist in the recipe (no duplicate ingredient_name).
        """
        # Check if recipe exists
        recipe = self.recipes.get(recipe_id)
        if recipe is None:
            return {"success": False, "error": "Recipe not found."}

        if not ingredient_name or ingredient_name.strip() == "":
            return {"success": False, "error": "Ingredient name must not be empty."}

        if not unit or unit.strip() == "":
            return {"success": False, "error": "Ingredient unit must not be empty."}

        if not isinstance(quantity, (int, float)) or quantity <= 0:
            return {"success": False, "error": "Ingredient quantity must be positive."}

        # Check for duplicate ingredient (by name)
        for ingr in recipe["ingredient_list"]:
            if ingr["ingredient_name"].lower() == ingredient_name.strip().lower():
                return {"success": False, "error": "Ingredient already exists in recipe."}

        new_ingredient = {
            "ingredient_name": ingredient_name.strip(),
            "quantity": quantity,
            "unit": unit.strip()
        }
        recipe["ingredient_list"].append(new_ingredient)
        return {"success": True, "message": f"Ingredient added to recipe {recipe_id}."}

    def remove_ingredient_from_recipe(self, recipe_id: str, ingredient_name: str) -> dict:
        """
        Remove an ingredient by name from a recipe's ingredient list.

        Args:
            recipe_id (str): ID of the recipe to modify.
            ingredient_name (str): Name of the ingredient to remove.

        Returns:
            dict: 
                - On success: {"success": True, "message": "Ingredient '<ingredient>' removed from recipe '<id>'."}
                - On failure: {"success": False, "error": "<reason>"}

        Constraints:
            - The recipe must exist.
            - The ingredient must exist in the recipe's ingredient list.
            - The recipe cannot have an empty ingredient list after removal.
        """
        # Check if recipe exists
        recipe = self.recipes.get(recipe_id)
        if not recipe:
            return {"success": False, "error": f"Recipe '{recipe_id}' does not exist."}
    
        # Find ingredient by name
        orig_count = len(recipe["ingredient_list"])
        new_ingredient_list = [
            ing for ing in recipe["ingredient_list"]
            if ing["ingredient_name"] != ingredient_name
        ]
        if len(new_ingredient_list) == orig_count:
            return {"success": False, "error": f"Ingredient '{ingredient_name}' not found in recipe '{recipe_id}'."}
        if not new_ingredient_list:
            return {"success": False, "error": "Cannot remove the last ingredient: ingredient list must not be empty."}

        # Update recipe's ingredient list
        recipe["ingredient_list"] = new_ingredient_list
        self.recipes[recipe_id] = recipe

        return {
            "success": True,
            "message": f"Ingredient '{ingredient_name}' removed from recipe '{recipe_id}'."
        }

    def edit_ingredient_in_recipe(
        self,
        recipe_id: str,
        old_ingredient_name: str,
        new_ingredient_name: str,
        new_quantity: float,
        new_unit: str
    ) -> dict:
        """
        Update the details (name, quantity, unit) of a specific ingredient in a recipe.

        Args:
            recipe_id (str): The identifier for the recipe.
            old_ingredient_name (str): Current name of the ingredient to update.
            new_ingredient_name (str): New name for the ingredient.
            new_quantity (float): New quantity value; must be positive.
            new_unit (str): New unit for the ingredient (non-empty).

        Returns:
            dict: {
                "success": True,
                "message": "Ingredient updated in recipe."
            }
            or
            dict: {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - recipe_id must exist.
            - old_ingredient_name must exist in the ingredient_list.
            - new_quantity must be positive.
            - new_ingredient_name and new_unit must be non-empty.
        """
        # Validate recipe existence
        recipe = self.recipes.get(recipe_id)
        if recipe is None:
            return {"success": False, "error": "Recipe not found."}

        # Validate new ingredient values
        if not new_ingredient_name.strip():
            return {"success": False, "error": "Ingredient name cannot be empty."}
        if not new_unit.strip():
            return {"success": False, "error": "Ingredient unit cannot be empty."}
        if new_quantity <= 0:
            return {"success": False, "error": "Ingredient quantity must be positive."}

        # Find and edit ingredient
        found = False
        for ingredient in recipe["ingredient_list"]:
            if ingredient["ingredient_name"] == old_ingredient_name:
                ingredient["ingredient_name"] = new_ingredient_name
                ingredient["quantity"] = new_quantity
                ingredient["unit"] = new_unit
                found = True
                break

        if not found:
            return {"success": False, "error": "Ingredient not found in recipe."}

        return {"success": True, "message": "Ingredient updated in recipe."}

    def validate_recipe_constraints(self, recipe: RecipeInfo) -> dict:
        """
        Check whether the provided recipe meets all system validity constraints.

        Args:
            recipe (RecipeInfo): Full info of the recipe to validate.

        Returns:
            dict:
                success (bool): True if valid, False if invalid
                message (str): If valid, human-readable message
                error (list): If invalid, list of reasons the recipe failed validation

        Constraints checked:
            - recipe_id must be present
            - ingredient_list must be non-empty
            - title must be present (non-empty)
            - instructions must be present (non-empty)
        """
        errors = []

        # Check recipe_id presence
        recipe_id = recipe.get("recipe_id")
        if not recipe_id or not isinstance(recipe_id, str):
            errors.append("Missing or invalid recipe_id.")

        # Check title presence
        title = recipe.get("title")
        if not title or not isinstance(title, str) or title.strip() == "":
            errors.append("Recipe title is missing or empty.")

        # Check instructions presence
        instructions = recipe.get("instructions")
        if not instructions or not isinstance(instructions, str) or instructions.strip() == "":
            errors.append("Recipe instructions are missing or empty.")

        # Check ingredient_list non-empty
        ingredient_list = recipe.get("ingredient_list")
        if not isinstance(ingredient_list, list) or len(ingredient_list) == 0:
            errors.append("Ingredient list is empty or missing.")

        if errors:
            return { "success": False, "error": errors }
        return { "success": True, "message": "Recipe is valid" }


class RecipeManagementSystem(BaseEnv):
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

    def get_recipe_by_id(self, **kwargs):
        return self._call_inner_tool('get_recipe_by_id', kwargs)

    def list_all_recipes(self, **kwargs):
        return self._call_inner_tool('list_all_recipes', kwargs)

    def search_recipes_by_title(self, **kwargs):
        return self._call_inner_tool('search_recipes_by_title', kwargs)

    def filter_recipes_by_cuisine(self, **kwargs):
        return self._call_inner_tool('filter_recipes_by_cuisine', kwargs)

    def filter_recipes_by_tag(self, **kwargs):
        return self._call_inner_tool('filter_recipes_by_tag', kwargs)

    def filter_recipes_by_difficulty(self, **kwargs):
        return self._call_inner_tool('filter_recipes_by_difficulty', kwargs)

    def filter_recipes_by_prep_time(self, **kwargs):
        return self._call_inner_tool('filter_recipes_by_prep_time', kwargs)

    def get_ingredient_list_for_recipe(self, **kwargs):
        return self._call_inner_tool('get_ingredient_list_for_recipe', kwargs)

    def add_recipe(self, **kwargs):
        return self._call_inner_tool('add_recipe', kwargs)

    def edit_recipe(self, **kwargs):
        return self._call_inner_tool('edit_recipe', kwargs)

    def delete_recipe(self, **kwargs):
        return self._call_inner_tool('delete_recipe', kwargs)

    def add_ingredient_to_recipe(self, **kwargs):
        return self._call_inner_tool('add_ingredient_to_recipe', kwargs)

    def remove_ingredient_from_recipe(self, **kwargs):
        return self._call_inner_tool('remove_ingredient_from_recipe', kwargs)

    def edit_ingredient_in_recipe(self, **kwargs):
        return self._call_inner_tool('edit_ingredient_in_recipe', kwargs)

    def validate_recipe_constraints(self, **kwargs):
        return self._call_inner_tool('validate_recipe_constraints', kwargs)
