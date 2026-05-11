# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import datetime



class IngredientInfo(TypedDict):
    ingredient_id: str
    name: str
    quantity: float
    unit: str
    nutrition_facts: dict  # Further schema can be established as needed

class CuisineInfo(TypedDict):
    cuisine_id: str
    name: str
    region: str

class RecipeInfo(TypedDict):
    recipe_id: str
    name: str
    cuisine_type: List[str]  # List of cuisine IDs
    preparation_instructions: str
    ingredients: List[IngredientInfo]
    nutritional_information: dict  # Further schema can be established as needed
    tags: List[str]
    source: str
    creation_date: str
    update_date: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Environment representing a recipe management and search API.
        """
        # Recipes: {recipe_id: RecipeInfo}
        self.recipes: Dict[str, RecipeInfo] = {}

        # Ingredients: {ingredient_id: IngredientInfo}
        self.ingredients: Dict[str, IngredientInfo] = {}

        # Cuisines: {cuisine_id: CuisineInfo}
        self.cuisines: Dict[str, CuisineInfo] = {}

        # --- Constraints ---
        # - Each recipe must have at least one ingredient.
        # - Each recipe must belong to at least one cuisine type.
        # - Ingredient names must be unique per recipe.
        # - Recipe IDs are globally unique.
        # - Ingredient quantity and unit must be specified per ingredient in each recipe.

    def list_recipes(
        self, 
        cuisine_type: list = None, 
        tags: list = None, 
        limit: int = 20, 
        offset: int = 0
    ) -> dict:
        """
        Retrieve a paginated or limited list of recipes, optionally filtered by cuisine_type and tags.

        Args:
            cuisine_type (list, optional): List of cuisine IDs to filter by. Recipe must have at least one of these.
            tags (list, optional): List of tags to filter by. Recipe must include all provided tags.
            limit (int, optional): Max number of recipes to return (default: 20).
            offset (int, optional): Starting index for result pagination (default: 0).

        Returns:
            dict:
                - On success: {"success": True, "data": [RecipeInfo, ...]}
                - On error: {"success": False, "error": str}
        """
        if limit is not None and (not isinstance(limit, int) or limit < 0):
            return {"success": False, "error": "Limit must be a non-negative integer"}
        if offset is not None and (not isinstance(offset, int) or offset < 0):
            return {"success": False, "error": "Offset must be a non-negative integer"}
        if cuisine_type is not None and not isinstance(cuisine_type, list):
            return {"success": False, "error": "cuisine_type must be a list if provided"}
        if tags is not None and not isinstance(tags, list):
            return {"success": False, "error": "tags must be a list if provided"}

        filtered_recipes = list(self.recipes.values())

        # Filter by cuisine_type (match any listed cuisine_type)
        if cuisine_type:
            filtered_recipes = [
                r for r in filtered_recipes
                if any(c in r["cuisine_type"] for c in cuisine_type)
            ]
        # Filter by tags (must include all provided tags)
        if tags:
            filtered_recipes = [
                r for r in filtered_recipes
                if all(tag in r.get("tags", []) for tag in tags)
            ]

        # Apply pagination/limiting
        paged_recipes = filtered_recipes[offset: offset + limit if limit != 0 else None] if limit else filtered_recipes[offset:]

        return {"success": True, "data": paged_recipes}

    def get_recipe_by_id(self, recipe_id: str) -> dict:
        """
        Retrieve the complete details of a recipe by its unique recipe_id.

        Args:
            recipe_id (str): The unique identifier of the recipe to retrieve.

        Returns:
            dict:
                - If found:
                    { "success": True, "data": RecipeInfo }
                - If not found or invalid:
                    { "success": False, "error": "Recipe not found" }

        Constraints:
            - recipe_id must exist in the system (self.recipes).
        """
        if not recipe_id or not isinstance(recipe_id, str):
            return { "success": False, "error": "Recipe not found" }
    
        recipe = self.recipes.get(recipe_id)
        if recipe is None:
            return { "success": False, "error": "Recipe not found" }
    
        return { "success": True, "data": recipe }

    def search_recipes_by_name(self, keyword: str) -> dict:
        """
        Retrieve recipes whose name matches or contains the specified keyword (case-insensitive).

        Args:
            keyword (str): The search keyword for recipe names. If empty, all recipes are returned.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[RecipeInfo],  # Recipes whose name contains the keyword (case-insensitive)
                }
            or
                {
                    "success": False,
                    "error": str  # Explanation (should rarely occur)
                }

        Notes:
            - If keyword is an empty string, all recipes will be returned.
        """
        if not isinstance(keyword, str):
            return { "success": False, "error": "Keyword must be a string" }

        keyword_lower = keyword.lower()
        result = []
        for recipe in self.recipes.values():
            if keyword_lower in recipe['name'].lower():
                result.append(recipe)
        return { "success": True, "data": result }

    def filter_recipes_by_ingredient(self, ingredient: str) -> dict:
        """
        Find all recipes that include a specific ingredient by name (case-insensitive) or ingredient_id.

        Args:
            ingredient (str): The ingredient name (case-insensitive) or ingredient_id to search for.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[RecipeInfo],  # Recipes containing the specified ingredient
                }
                or
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - The search key can be ingredient_id or ingredient name (case-insensitive).
            - If input is empty, the operation fails.
        """
        if not ingredient or not ingredient.strip():
            return { "success": False, "error": "Ingredient identifier or name must be provided" }

        ingredient_lower = ingredient.strip().lower()
        result = []
        for recipe in self.recipes.values():
            for ing in recipe["ingredients"]:
                if (
                    ing["ingredient_id"] == ingredient
                    or ing["name"].strip().lower() == ingredient_lower
                ):
                    result.append(recipe)
                    break  # Only add recipe once

        return { "success": True, "data": result }

    def filter_recipes_by_cuisine(self, cuisine_id: str) -> dict:
        """
        Retrieve recipes that belong to a specific cuisine type.

        Args:
            cuisine_id (str): The unique identifier for the cuisine to filter recipes by.

        Returns:
            dict: {
                "success": True,
                "data": List[RecipeInfo],  # List of matched recipes (may be empty if none)
            }
            or
            {
                "success": False,
                "error": str  # If cuisine is not found
            }

        Constraints:
            - cuisine_id must exist in the system.
            - Each recipe has at least one cuisine_type (enforced elsewhere).
        """
        if cuisine_id not in self.cuisines:
            return {"success": False, "error": "Cuisine does not exist"}

        matched = [
            recipe_info for recipe_info in self.recipes.values()
            if cuisine_id in recipe_info.get("cuisine_type", [])
        ]

        return {"success": True, "data": matched}

    def get_ingredient_by_id(self, ingredient_id: str) -> dict:
        """
        Retrieve ingredient details by its unique ingredient_id.

        Args:
            ingredient_id (str): The unique identifier of the ingredient.

        Returns:
            dict: {
                "success": True,
                "data": IngredientInfo  # Detailed information if found
            }
            or
            {
                "success": False,
                "error": str  # Error message if not found
            }

        Constraints:
            - ingredient_id must exist in the environment for a successful result.
        """
        ingredient = self.ingredients.get(ingredient_id)
        if not ingredient:
            return { "success": False, "error": "Ingredient not found" }
        return { "success": True, "data": ingredient }

    def list_cuisines(self) -> dict:
        """
        Retrieve the list of all available cuisines.

        Returns:
            dict:
                - success (bool): True if operation succeeded.
                - data (List[CuisineInfo]): A list (possibly empty) of all available cuisine information.
            Example:
                {
                    "success": True,
                    "data": [CuisineInfo, ...]
                }

        Constraints:
            - No input is required.
            - Returns all cuisines present in the system.
        """
        cuisines_list = list(self.cuisines.values()) if hasattr(self, "cuisines") else []
        return {
            "success": True,
            "data": cuisines_list
        }

    def get_cuisine_by_id(self, cuisine_id: str) -> dict:
        """
        Retrieve details for a cuisine by its cuisine_id.

        Args:
            cuisine_id (str): The unique ID of the cuisine.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": CuisineInfo  # Information about the cuisine
                    }
                On failure (not found):
                    {
                        "success": False,
                        "error": "Cuisine not found"
                    }

        Constraints:
            - The cuisine_id must exist in the current list of cuisines.
        """
        cuisine = self.cuisines.get(cuisine_id)
        if cuisine is None:
            return {"success": False, "error": "Cuisine not found"}
        return {"success": True, "data": cuisine}

    def get_recipe_ingredients(self, recipe_id: str) -> dict:
        """
        List all ingredient details (with quantity, unit, etc.) for a specific recipe.

        Args:
            recipe_id (str): Unique identifier of the recipe.

        Returns:
            dict: {
                "success": True,
                "data": List[IngredientInfo],  # List of all ingredients (may be empty if data is inconsistent)
            }
            or
            {
                "success": False,
                "error": str  # Reason why retrieval failed (e.g. recipe not found)
            }

        Constraints:
            - Recipe must exist (if not, return error)
        """
        recipe = self.recipes.get(recipe_id)
        if recipe is None:
            return {"success": False, "error": "Recipe not found"}

        ingredients = recipe.get("ingredients", [])
        return {"success": True, "data": ingredients}

    def get_recipe_nutritional_information(self, recipe_id: str) -> dict:
        """
        Retrieve the nutritional information for a given recipe, by recipe ID.

        Args:
            recipe_id (str): The unique ID of the recipe.

        Returns:
            dict: {
                "success": True,
                "data": dict  # nutritional_information of the recipe
            }
            or
            {
                "success": False,
                "error": str  # e.g., "Recipe not found"
            }

        Constraints:
            - The recipe_id must exist in the system.
        """
        recipe = self.recipes.get(recipe_id)
        if recipe is None:
            return { "success": False, "error": "Recipe not found" }
        return { "success": True, "data": recipe.get("nutritional_information", {}) }

    def add_recipe(
        self,
        recipe_id: str,
        name: str,
        cuisine_type: list,
        preparation_instructions: str,
        ingredients: list,
        nutritional_information: dict,
        tags: list,
        source: str,
        creation_date: str,
        update_date: str
    ) -> dict:
        """
        Create and add a new recipe with all required fields to the API.

        Args:
            recipe_id (str): Globally unique identifier for the recipe.
            name (str): The name of the recipe.
            cuisine_type (List[str]): List of cuisine IDs this recipe belongs to. Must not be empty and must reference valid cuisines.
            preparation_instructions (str): Preparation instructions.
            ingredients (List[IngredientInfo]): List of ingredient info. Must not be empty, names must be unique within this list.
            nutritional_information (dict): Nutrition details of the recipe.
            tags (List[str]): List of tags or keywords.
            source (str): Provenance or source string.
            creation_date (str): Recipe creation date string.
            update_date (str): Latest update date string.

        Returns:
            dict: Success or error dict.
                - On success: {'success': True, 'message': "..."}
                - On failure: {'success': False, 'error': "..."}
    
        Constraints:
            - Recipe ID must be unique.
            - At least one ingredient, and names within must be unique.
            - At least one existing cuisine_type.
            - Each ingredient entry must have name, quantity (float), unit (str), and nutrition_facts (dict).
        """
        # Check uniqueness of recipe ID
        if recipe_id in self.recipes:
            return {"success": False, "error": "Recipe ID already exists."}

        # Check that cuisine_type is a non-empty list and the cuisines exist
        if not isinstance(cuisine_type, list) or len(cuisine_type) == 0:
            return {"success": False, "error": "At least one cuisine type must be specified."}
        for cid in cuisine_type:
            if cid not in self.cuisines:
                return {"success": False, "error": f"Cuisine ID {cid} does not exist."}

        # Check that ingredients is a non-empty list
        if not isinstance(ingredients, list) or len(ingredients) == 0:
            return {"success": False, "error": "At least one ingredient must be specified."}
        # Check unique ingredient names in this recipe
        ingredient_names = set()
        for idx, ingr in enumerate(ingredients):
            if not isinstance(ingr, dict):
                return {"success": False, "error": f"Ingredient at index {idx} is not a valid dict."}
            req_fields = ["ingredient_id", "name", "quantity", "unit", "nutrition_facts"]
            for field in req_fields:
                if field not in ingr:
                    return {"success": False, "error": f"Ingredient missing required field: {field}"}
            # Check quantity is float (or can be converted)
            try:
                float(ingr["quantity"])
            except (ValueError, TypeError):
                return {"success": False, "error": f"Invalid quantity for ingredient '{ingr.get('name', '?')}'"}
            # Check unit is a string
            if not isinstance(ingr["unit"], str):
                return {"success": False, "error": f"Invalid unit for ingredient '{ingr.get('name', '?')}'"}
            # Name uniqueness
            ingr_name = ingr["name"]
            if ingr_name in ingredient_names:
                return {"success": False, "error": f"Duplicate ingredient name: {ingr_name}"}
            ingredient_names.add(ingr_name)

        # Construct new RecipeInfo dict
        new_recipe = {
            "recipe_id": recipe_id,
            "name": name,
            "cuisine_type": cuisine_type,
            "preparation_instructions": preparation_instructions,
            "ingredients": ingredients,
            "nutritional_information": nutritional_information,
            "tags": tags,
            "source": source,
            "creation_date": creation_date,
            "update_date": update_date
        }

        self.recipes[recipe_id] = new_recipe

        return {"success": True, "message": f"Recipe '{name}' ({recipe_id}) added successfully."}

    def update_recipe(
        self,
        recipe_id: str,
        name: str = None,
        cuisine_type: list = None,
        preparation_instructions: str = None,
        ingredients: list = None,
        nutritional_information: dict = None,
        tags: list = None,
        source: str = None
    ) -> dict:
        """
        Modify an existing recipe, enforcing constraints:
        - Recipe must exist.
        - Recipe must have at least one ingredient.
        - Ingredient names must be unique within the recipe.
        - Ingredient quantity and unit must be specified per ingredient.
        - Recipe must belong to at least one cuisine type.

        Args:
            recipe_id (str): ID of the recipe to update.
            name (str, optional): New recipe name.
            cuisine_type (list, optional): List of cuisine IDs.
            preparation_instructions (str, optional): Updated instructions.
            ingredients (list of IngredientInfo, optional): New list of ingredients.
            nutritional_information (dict, optional): Nutrition facts.
            tags (list, optional): Tags for the recipe.
            source (str, optional): Recipe source.

        Returns:
            dict: Success or error description.
        """
        if recipe_id not in self.recipes:
            return { "success": False, "error": "Recipe not found." }

        recipe = self.recipes[recipe_id].copy()  # .copy() so we keep existing if error
        # Update fields if provided
        if name is not None:
            recipe["name"] = name
        if cuisine_type is not None:
            recipe["cuisine_type"] = cuisine_type
        if preparation_instructions is not None:
            recipe["preparation_instructions"] = preparation_instructions
        if ingredients is not None:
            recipe["ingredients"] = ingredients
        if nutritional_information is not None:
            recipe["nutritional_information"] = nutritional_information
        if tags is not None:
            recipe["tags"] = tags
        if source is not None:
            recipe["source"] = source

        # Constraint checks after update
        # 1. Must have at least one ingredient
        ingr_list = recipe.get("ingredients", [])
        if not ingr_list or len(ingr_list) == 0:
            return { "success": False, "error": "A recipe must have at least one ingredient." }

        # 2. Ingredient names must be unique per recipe
        names = [ingr.get("name") for ingr in ingr_list]
        if len(set(names)) != len(names):
            return { "success": False, "error": "Ingredient names must be unique within the recipe." }

        # 3. Ingredient quantity and unit must be specified for each
        for ingr in ingr_list:
            if (
                ingr.get("quantity") is None or ingr.get("unit") is None or 
                (isinstance(ingr.get("unit"), str) and ingr.get("unit").strip() == "") or
                (isinstance(ingr.get("quantity"), (int, float)) and ingr.get("quantity") <= 0)
            ):
                return { "success": False, "error": "Each ingredient must have specified quantity and unit." }

        # 4. Must belong to at least one cuisine type
        cuisine_ids = recipe.get("cuisine_type", [])
        if not cuisine_ids or len(cuisine_ids) == 0:
            return { "success": False, "error": "Recipe must belong to at least one cuisine type." }
        has_cuisine_registry = isinstance(getattr(self, "cuisines", None), dict) and len(self.cuisines) > 0
        if has_cuisine_registry:
            for cuisine_id in cuisine_ids:
                if cuisine_id not in self.cuisines:
                    return { "success": False, "error": f"Cuisine ID {cuisine_id} does not exist." }

        # If all checks pass, save the changes and stamp update date
        recipe["update_date"] = datetime.datetime.now().isoformat()
        self.recipes[recipe_id] = recipe

        return { "success": True, "message": "Recipe updated successfully." }

    def delete_recipe(self, recipe_id: str) -> dict:
        """
        Remove a recipe from the collection by its unique recipe_id.

        Args:
            recipe_id (str): The unique identifier of the recipe to delete.

        Returns:
            dict:
                - On success: {"success": True, "message": "Recipe deleted successfully"}
                - On failure: {"success": False, "error": "Recipe not found"}

        Constraints:
            - The recipe must exist in the collection.
            - Only the recipe itself is removed; referenced ingredients and cuisine types remain.
        """
        if recipe_id not in self.recipes:
            return { "success": False, "error": "Recipe not found" }

        del self.recipes[recipe_id]
        return { "success": True, "message": "Recipe deleted successfully" }

    def add_ingredient_to_recipe(
        self, 
        recipe_id: str, 
        ingredient_id: str, 
        name: str, 
        quantity: float, 
        unit: str, 
        nutrition_facts: dict
    ) -> dict:
        """
        Add a new ingredient with specified quantity and unit to an existing recipe.

        Args:
            recipe_id (str): The ID of the recipe to modify.
            ingredient_id (str): The ingredient ID for the recipe entry. It may reference an
                existing global ingredient catalog item, or it may be a brand-new global ID.
            name (str): The name of the ingredient (must be unique in the target recipe).
            quantity (float): The amount of the ingredient.
            unit (str): The unit of measurement for the quantity.
            nutrition_facts (dict): Nutrition facts for this ingredient.

        Returns:
            dict:
                - On success:
                    { "success": True, "message": "Ingredient added to recipe <recipe_id>" }
                - On failure:
                    { "success": False, "error": "<reason>" }

        Constraints:
            - Recipe must exist.
            - Ingredient names must be unique in the recipe.
            - Ingredient ID must not already appear in the target recipe.
            - If ingredient_id already exists in the global ingredient catalog, it may be reused
              as a recipe reference; otherwise it must be globally unique.
            - Both quantity and unit must be provided (and quantity should be positive).
        """

        # Verify recipe exists
        if recipe_id not in self.recipes:
            return { "success": False, "error": "Recipe does not exist" }

        recipe = self.recipes[recipe_id]

        # Check if ingredient ID already exists in the target recipe
        for ingredient in recipe["ingredients"]:
            if ingredient["ingredient_id"] == ingredient_id:
                return { "success": False, "error": "Ingredient ID already exists in recipe" }

        # Check if ingredient name already exists in recipe
        for ingredient in recipe["ingredients"]:
            if ingredient["name"].strip().lower() == name.strip().lower():
                return { "success": False, "error": "Ingredient name already exists in recipe" }

        # Allow reusing an existing catalog ingredient ID as a recipe reference, but keep the
        # catalog/name mapping coherent if the ID is already defined globally.
        catalog_ingredient = self.ingredients.get(ingredient_id)
        if catalog_ingredient is not None:
            catalog_name = str(catalog_ingredient.get("name", "")).strip().lower()
            if catalog_name and catalog_name != name.strip().lower():
                return { "success": False, "error": "Ingredient ID conflicts with existing catalog ingredient" }

        # Validate quantity and unit
        if (quantity is None or unit is None or str(unit).strip() == "" or
                not isinstance(quantity, (int, float)) or quantity <= 0):
            return { "success": False, "error": "Ingredient quantity and unit must be specified" }

        # Construct ingredient info
        new_ingredient = {
            "ingredient_id": ingredient_id,
            "name": name,
            "quantity": quantity,
            "unit": unit,
            "nutrition_facts": nutrition_facts if nutrition_facts is not None else {}
        }

        # Add to global ingredients registry only for brand-new ingredient IDs.
        if catalog_ingredient is None:
            self.ingredients[ingredient_id] = new_ingredient

        # Add to recipe's ingredients list
        recipe["ingredients"].append(new_ingredient)

        return { "success": True, "message": f"Ingredient added to recipe {recipe_id}" }

    def update_ingredient_in_recipe(
        self,
        recipe_id: str,
        ingredient_id: str,
        quantity: float = None,
        unit: str = None,
        nutrition_facts: dict = None
    ) -> dict:
        """
        Modify the quantity, unit, or nutrition facts of an ingredient in a recipe.

        Args:
            recipe_id (str): The ID of the recipe to update.
            ingredient_id (str): The ID of the ingredient to modify within the recipe.
            quantity (float, optional): The new quantity for the ingredient.
            unit (str, optional): The new unit for the ingredient.
            nutrition_facts (dict, optional): The new nutrition facts for the ingredient.

        Returns:
            dict: {
                "success": True,
                "message": "Ingredient updated in recipe."
            }
            OR
            {
                "success": False,
                "error": "Reason for failure."
            }

        Constraints:
            - Both 'recipe_id' and 'ingredient_id' must exist.
            - The ingredient must be part of the specified recipe.
            - After update, 'quantity' (float) and 'unit' (str, not empty) must be present for the ingredient.
        """
        # Check if recipe exists
        recipe = self.recipes.get(recipe_id)
        if not recipe:
            return { "success": False, "error": "Recipe does not exist." }

        # Find ingredient in recipe
        ingredient_list = recipe.get("ingredients", [])
        ingredient = None
        for ing in ingredient_list:
            if ing["ingredient_id"] == ingredient_id:
                ingredient = ing
                break

        if ingredient is None:
            return { "success": False, "error": "Ingredient not found in recipe." }

        # Update quantity if provided
        if quantity is not None:
            if not isinstance(quantity, (float, int)):
                return { "success": False, "error": "Invalid quantity: must be a number." }
            ingredient["quantity"] = float(quantity)

        # Update unit if provided
        if unit is not None:
            if not isinstance(unit, str) or not unit.strip():
                return { "success": False, "error": "Invalid unit: must be a non-empty string." }
            ingredient["unit"] = unit.strip()

        # Update nutrition_facts if provided
        if nutrition_facts is not None:
            if not isinstance(nutrition_facts, dict):
                return { "success": False, "error": "Invalid nutrition_facts: must be a dict." }
            ingredient["nutrition_facts"] = nutrition_facts

        # After updates, ensure quantity and unit are set and valid
        if "quantity" not in ingredient or not isinstance(ingredient["quantity"], (float, int)):
            return { "success": False, "error": "Ingredient must have a valid quantity after update." }
        if "unit" not in ingredient or not isinstance(ingredient["unit"], str) or not ingredient["unit"].strip():
            return { "success": False, "error": "Ingredient must have a valid unit after update." }

        # "Persist" update (as we updated the dict in place)
        return { "success": True, "message": "Ingredient updated in recipe." }

    def remove_ingredient_from_recipe(self, recipe_id: str, ingredient_id: str) -> dict:
        """
        Remove an ingredient from a specified recipe, ensuring the recipe retains at least one ingredient.

        Args:
            recipe_id (str): ID of the recipe from which to remove the ingredient.
            ingredient_id (str): ID of the ingredient to remove.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Ingredient <ingredient_id> removed from recipe <recipe_id>"
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason for failure
                    }

        Constraints:
            - The recipe must exist.
            - The ingredient must be present in the specified recipe.
            - A recipe must always have at least one ingredient.
        """

        # Check recipe existence
        recipe = self.recipes.get(recipe_id)
        if recipe is None:
            return { "success": False, "error": f"Recipe {recipe_id} does not exist" }

        ingredients = recipe.get("ingredients", [])
        # Locate ingredient by ID in the recipe
        matching = [i for i in ingredients if i["ingredient_id"] == ingredient_id]

        if not matching:
            return { "success": False, "error": f"Ingredient {ingredient_id} is not part of recipe {recipe_id}" }

        # Removing all occurrences (should be exactly one due to design, but robust against schema issues)
        new_ingredients = [i for i in ingredients if i["ingredient_id"] != ingredient_id]

        # Constraint: a recipe must have at least one ingredient left afterwards
        if len(new_ingredients) == 0:
            return {
                "success": False,
                "error": f"Cannot remove ingredient; recipe {recipe_id} must have at least one ingredient"
            }

        # Perform update
        recipe["ingredients"] = new_ingredients
        self.recipes[recipe_id] = recipe

        return {
            "success": True,
            "message": f"Ingredient {ingredient_id} removed from recipe {recipe_id}"
        }

    def add_cuisine(self, cuisine_id: str, name: str, region: str) -> dict:
        """
        Add a new cuisine type to the database.

        Args:
            cuisine_id (str): Unique identifier for the cuisine.
            name (str): The name of the cuisine.
            region (str): The geographical region of the cuisine.

        Returns:
            dict: {
                "success": True,
                "message": "Cuisine added successfully"
            } on success,
            {
                "success": False,
                "error": <error_reason>
            } on failure.

        Constraints:
            - Cuisine IDs must be unique.
            - All fields are required (must not be empty).
        """
        if not cuisine_id or not name or not region:
            return { "success": False, "error": "Missing required cuisine fields" }

        if cuisine_id in self.cuisines:
            return { "success": False, "error": "Cuisine ID already exists" }

        new_cuisine: CuisineInfo = {
            "cuisine_id": cuisine_id,
            "name": name,
            "region": region
        }

        self.cuisines[cuisine_id] = new_cuisine
        return { "success": True, "message": "Cuisine added successfully" }

    def update_cuisine(self, cuisine_id: str, name: str = None, region: str = None) -> dict:
        """
        Modify an existing cuisine’s name or region.

        Args:
            cuisine_id (str): The ID of the cuisine to update.
            name (str, optional): The new name for the cuisine. If not provided, name will not be changed.
            region (str, optional): The new region for the cuisine. If not provided, region will not be changed.

        Returns:
            dict:
                On success: { "success": True, "message": "Cuisine updated successfully." }
                On failure: { "success": False, "error": "Cuisine not found" | "No update parameters specified" }

        Constraints:
            - cuisine_id must exist in self.cuisines.
            - At least one of name or region must be provided.
        """
        if cuisine_id not in self.cuisines:
            return { "success": False, "error": "Cuisine not found" }

        if name is None and region is None:
            return { "success": False, "error": "No update parameters specified" }

        cuisine_info = self.cuisines[cuisine_id]

        if name is not None:
            cuisine_info["name"] = name
        if region is not None:
            cuisine_info["region"] = region

        self.cuisines[cuisine_id] = cuisine_info

        return { "success": True, "message": "Cuisine updated successfully." }

    def assign_cuisine_to_recipe(self, recipe_id: str, cuisine_id: str) -> dict:
        """
        Assign an additional cuisine type (by cuisine_id) to a recipe.

        Args:
            recipe_id (str): Unique identifier of the recipe.
            cuisine_id (str): Unique identifier of the cuisine to assign.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "message": "Cuisine <cuisine_id> assigned to recipe <recipe_id>."
                    }
                - On failure:
                    {
                        "success": False,
                        "error": "Error description"
                    }

        Constraints:
            - Both the recipe and cuisine must exist.
            - Each recipe must always have at least one cuisine (constraint maintained by only ever adding).
            - If the cuisine is already assigned, operation is idempotent: report success.
        """
        # Validate recipe existence
        if recipe_id not in self.recipes:
            return {"success": False, "error": f"Recipe {recipe_id} does not exist."}
        # Validate cuisine existence
        if cuisine_id not in self.cuisines:
            return {"success": False, "error": f"Cuisine {cuisine_id} does not exist."}
        # Get recipe info
        recipe = self.recipes[recipe_id]
        # Idempotency: already assigned?
        if cuisine_id in recipe["cuisine_type"]:
            return {
                "success": True, 
                "message": f"Cuisine {cuisine_id} is already assigned to recipe {recipe_id}."
            }
        # Assign cuisine
        recipe["cuisine_type"].append(cuisine_id)
        self.recipes[recipe_id] = recipe
        return {
            "success": True,
            "message": f"Cuisine {cuisine_id} assigned to recipe {recipe_id}."
        }


class RecipeManagementAPI(BaseEnv):
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

    def list_recipes(self, **kwargs):
        return self._call_inner_tool('list_recipes', kwargs)

    def get_recipe_by_id(self, **kwargs):
        return self._call_inner_tool('get_recipe_by_id', kwargs)

    def search_recipes_by_name(self, **kwargs):
        return self._call_inner_tool('search_recipes_by_name', kwargs)

    def filter_recipes_by_ingredient(self, **kwargs):
        return self._call_inner_tool('filter_recipes_by_ingredient', kwargs)

    def filter_recipes_by_cuisine(self, **kwargs):
        return self._call_inner_tool('filter_recipes_by_cuisine', kwargs)

    def get_ingredient_by_id(self, **kwargs):
        return self._call_inner_tool('get_ingredient_by_id', kwargs)

    def list_cuisines(self, **kwargs):
        return self._call_inner_tool('list_cuisines', kwargs)

    def get_cuisine_by_id(self, **kwargs):
        return self._call_inner_tool('get_cuisine_by_id', kwargs)

    def get_recipe_ingredients(self, **kwargs):
        return self._call_inner_tool('get_recipe_ingredients', kwargs)

    def get_recipe_nutritional_information(self, **kwargs):
        return self._call_inner_tool('get_recipe_nutritional_information', kwargs)

    def add_recipe(self, **kwargs):
        return self._call_inner_tool('add_recipe', kwargs)

    def update_recipe(self, **kwargs):
        return self._call_inner_tool('update_recipe', kwargs)

    def delete_recipe(self, **kwargs):
        return self._call_inner_tool('delete_recipe', kwargs)

    def add_ingredient_to_recipe(self, **kwargs):
        return self._call_inner_tool('add_ingredient_to_recipe', kwargs)

    def update_ingredient_in_recipe(self, **kwargs):
        return self._call_inner_tool('update_ingredient_in_recipe', kwargs)

    def remove_ingredient_from_recipe(self, **kwargs):
        return self._call_inner_tool('remove_ingredient_from_recipe', kwargs)

    def add_cuisine(self, **kwargs):
        return self._call_inner_tool('add_cuisine', kwargs)

    def update_cuisine(self, **kwargs):
        return self._call_inner_tool('update_cuisine', kwargs)

    def assign_cuisine_to_recipe(self, **kwargs):
        return self._call_inner_tool('assign_cuisine_to_recipe', kwargs)
