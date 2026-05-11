# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict



# Represents a manufacturer or brand of vehicles
class CarBrandInfo(TypedDict):
    brand_id: str
    name: str

# Represents a specific car model linked to a car brand
class CarModelInfo(TypedDict):
    model_id: str
    brand_id: str  # FK to CarBrand
    name: str
    year: int
    type: str

# Represents an individual car instance
class CarUnitInfo(TypedDict):
    unit_id: str
    model_id: str  # FK to CarModel
    VIN: str
    availability_status: str
    location: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Car brands: {brand_id: CarBrandInfo}
        self.car_brands: Dict[str, CarBrandInfo] = {}
        # Car models: {model_id: CarModelInfo}
        self.car_models: Dict[str, CarModelInfo] = {}
        # Car units: {unit_id: CarUnitInfo}
        self.car_units: Dict[str, CarUnitInfo] = {}

        # Constraints:
        # - Each CarModel must be associated with a valid CarBrand (car_models[model_id]['brand_id'] in car_brands)
        # - Each CarUnit must be associated with a valid CarModel (car_units[unit_id]['model_id'] in car_models)
        # - availability_status of CarUnit records if the car is currently available
        # - Queries for available brands depend on at least one associated CarUnit being available

    def list_all_brands(self) -> dict:
        """
        Retrieve all car brands recorded in the transportation database system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[CarBrandInfo],  # List of all car brand info (may be empty if none in system)
            }
            or
            {
                "success": False,
                "error": str  # Description of the error
            }

        Constraints:
            - None; all stored brands are returned.
        """
        if not hasattr(self, "car_brands") or not isinstance(self.car_brands, dict):
            return { "success": False, "error": "Car brands data not available or corrupted." }

        result = list(self.car_brands.values())
        return { "success": True, "data": result }

    def get_brand_by_id(self, brand_id: str) -> dict:
        """
        Retrieve detailed information for a specific car brand using brand_id.

        Args:
            brand_id (str): The unique identifier for the car brand.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": CarBrandInfo  # All metadata for the brand
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason for failure, e.g., brand does not exist
                    }

        Constraints:
            - brand_id must exist in the car_brands dictionary.
        """
        brand = self.car_brands.get(brand_id)
        if not brand:
            return {"success": False, "error": f"Brand with id {brand_id} does not exist."}
        return {"success": True, "data": brand}

    def list_all_models(self) -> dict:
        """
        Retrieve all car models in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[CarModelInfo]  # List of all car models (may be empty)
            }
        """
        models = list(self.car_models.values())
        return { "success": True, "data": models }

    def list_models_by_brand(self, brand_id: str) -> dict:
        """
        List all car models associated with a specific brand.

        Args:
            brand_id (str): The unique identifier of the brand.

        Returns:
            dict:
                - On success: {"success": True, "data": List[CarModelInfo]}
                - On error:   {"success": False, "error": <reason>}
    
        Constraints:
            - The brand_id must exist in the car_brands.
        """
        if brand_id not in self.car_brands:
            return {"success": False, "error": "Brand does not exist"}

        models = [
            model_info for model_info in self.car_models.values()
            if model_info['brand_id'] == brand_id
        ]
        return {"success": True, "data": models}

    def get_model_by_id(self, model_id: str) -> dict:
        """
        Retrieve detailed information for a specific car model using model_id.

        Args:
            model_id (str): The model ID to look up.

        Returns:
            dict: {
                "success": True,
                "data": CarModelInfo  # If the model is found
            }
            or
            {
                "success": False,
                "error": str  # "Model not found" if model_id is invalid
            }

        Constraints:
            - model_id must exist in the database.
        """
        model = self.car_models.get(model_id)
        if not model:
            return {"success": False, "error": "Model not found"}
        return {"success": True, "data": model}

    def list_all_units(self) -> dict:
        """
        Retrieve all individual car units (inventory) in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[CarUnitInfo]  # List of all car units (may be empty)
            }

        Constraints:
            - No input; returns all CarUnitInfo records.
            - No failure; if no units, returns empty list.
        """
        all_units = list(self.car_units.values())
        return { "success": True, "data": all_units }

    def list_units_by_model(self, model_id: str) -> dict:
        """
        List all car units (inventory) associated with a specific car model.

        Args:
            model_id (str): The ID of the car model.

        Returns:
            dict: {
                "success": True,
                "data": List[CarUnitInfo]  # List of car units for the model (may be empty if none)
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g. model does not exist
            }

        Constraints:
            - The model_id must reference an existing CarModel.
        """
        if model_id not in self.car_models:
            return { "success": False, "error": "Car model does not exist" }

        units = [unit_info for unit_info in self.car_units.values()
                 if unit_info['model_id'] == model_id]

        return { "success": True, "data": units }

    def list_units_by_brand(self, brand_id: str) -> dict:
        """
        List all car units associated with a specific brand by aggregating units across all its models.

        Args:
            brand_id (str): The unique identifier for the CarBrand.

        Returns:
            dict: {
                "success": True,
                "data": List[CarUnitInfo],  # List of all car units linked to this brand
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., brand does not exist)
            }
    
        Constraints:
            - The brand_id must exist in the system.
        """
        if brand_id not in self.car_brands:
            return { "success": False, "error": "Brand does not exist" }

        # Find all model_ids belonging to this brand
        model_ids = { model['model_id'] for model in self.car_models.values() if model['brand_id'] == brand_id }

        # Gather all car units whose model_id is in this set
        units = [
            unit for unit in self.car_units.values()
            if unit['model_id'] in model_ids
        ]

        return { "success": True, "data": units }

    def get_unit_by_id(self, unit_id: str) -> dict:
        """
        Retrieve detailed information for a specific car unit using unit_id.

        Args:
            unit_id (str): The unique identifier of the car unit to retrieve.

        Returns:
            dict:
                success (bool): True if found, False otherwise.
                data (CarUnitInfo): Complete info of the found unit if success.
                error (str): Error message if not found.

        Constraints:
            - unit_id must correspond to an existing CarUnit in the database.
        """
        car_unit = self.car_units.get(unit_id)
        if car_unit is None:
            return { "success": False, "error": "Car unit not found" }

        return { "success": True, "data": car_unit }

    def filter_units_by_availability(self, availability_status: str) -> dict:
        """
        Filter and retrieve car units based on their availability_status.

        Args:
            availability_status (str): Desired status to filter car units by (e.g., "available", "rented").

        Returns:
            dict: {
                "success": True,
                "data": List[CarUnitInfo],  # possibly empty if no matches found
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - If there are no car units with the requested status, returns an empty list in "data".
            - No error for unknown status; strict checking of allowed status values is not enforced.
        """
        if not isinstance(availability_status, str) or not availability_status:
            return {"success": False, "error": "Invalid or empty availability_status parameter."}
    
        filtered_units = [
            unit for unit in self.car_units.values()
            if unit["availability_status"] == availability_status
        ]
        return {"success": True, "data": filtered_units}

    def list_available_brands(self) -> dict:
        """
        Retrieve all car brands (CarBrandInfo) that currently have at least one associated available car unit.
    
        Returns:
            dict: {
                "success": True,
                "data": List[CarBrandInfo]
            }
            or
            {
                "success": False,
                "error": str
            }
    
        Constraints:
            - Only brands with at least one associated available car unit are listed.
            - CarUnit must be associated with valid CarModel, CarModel with valid CarBrand.
        """
        # Step 1: Find model_ids for valid car models (just in case there is data inconsistency)
        valid_model_ids = set(self.car_models.keys())

        # Step 2: Find brand_ids for valid car brands
        valid_brand_ids = set(self.car_brands.keys())

        # Step 3: Track brands with at least one available car unit
        available_brand_ids = set()

        for unit in self.car_units.values():
            if unit["availability_status"] != "available":
                continue
            model_id = unit["model_id"]
            if model_id not in valid_model_ids:
                continue
            brand_id = self.car_models[model_id]["brand_id"]
            if brand_id in valid_brand_ids:
                available_brand_ids.add(brand_id)

        # Step 4: Collect CarBrandInfo for those brand_ids
        result = []
        for brand_id in available_brand_ids:
            brand_info = self.car_brands.get(brand_id)
            if brand_info:
                result.append(brand_info)

        return { "success": True, "data": result }

    def add_brand(self, brand_id: str, name: str) -> dict:
        """
        Add a new car brand to the transportation database.

        Args:
            brand_id (str): Unique identifier for the car brand.
            name (str): Name of the car brand.

        Returns:
            dict: 
                - { "success": True, "message": "Car brand added successfully" }
                - { "success": False, "error": "reason" }

        Constraints:
            - brand_id must be unique (not already present in car_brands).
            - name must be a non-empty string.
        """
        if not brand_id or not isinstance(brand_id, str):
            return {"success": False, "error": "Invalid or empty brand_id"}
        if not name or not isinstance(name, str):
            return {"success": False, "error": "Invalid or empty name"}
        if brand_id in self.car_brands:
            return {"success": False, "error": "Brand ID already exists"}

        self.car_brands[brand_id] = {
            "brand_id": brand_id,
            "name": name
        }
        return {"success": True, "message": "Car brand added successfully"}

    def update_brand(self, brand_id: str, name: str = None) -> dict:
        """
        Update the name (or other updatable fields) of an existing car brand.

        Args:
            brand_id (str): The unique identifier of the brand to update.
            name (str, optional): The new name for the brand.

        Returns:
            dict: {
                "success": True,
                "message": "Brand updated successfully."
            }
            or
            {
                "success": False,
                "error": "Car brand does not exist."
            }

        Constraints:
            - The brand must exist.
            - Only updates fields that exist in CarBrandInfo (here: "name").
        """
        if brand_id not in self.car_brands:
            return { "success": False, "error": "Car brand does not exist." }

        # Track if any field was updated
        updated = False

        if name is not None:
            self.car_brands[brand_id]['name'] = name
            updated = True

        # Even if no fields were updated (all arguments None), still "success" (no-op)
        return { "success": True, "message": "Brand updated successfully." }

    def delete_brand(self, brand_id: str) -> dict:
        """
        Delete a car brand if there are no car models associated.

        Args:
            brand_id (str): The unique identifier of the brand to delete.

        Returns:
            dict:
                { "success": True, "message": "Brand deleted." }
                or
                { "success": False, "error": "<reason>" }

        Constraints:
            - The specified brand must exist.
            - The brand cannot be deleted if any CarModel is associated with it.
        """
        # Check existence of brand
        if brand_id not in self.car_brands:
            return { "success": False, "error": "Brand does not exist." }
    
        # Check for associated models
        for model in self.car_models.values():
            if model["brand_id"] == brand_id:
                return { "success": False, "error": "Cannot delete brand: models are associated to this brand." }
    
        # Delete the brand
        del self.car_brands[brand_id]
        return { "success": True, "message": "Brand deleted." }

    def add_model(self, model_id: str, brand_id: str, name: str, year: int, type: str) -> dict:
        """
        Add a new car model associated with a valid car brand.

        Args:
            model_id (str): Unique identifier for the car model.
            brand_id (str): Existing car brand ID to associate with the model.
            name (str): Name of the car model.
            year (int): Year of the car model.
            type (str): Type/category of the car model.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Car model added successfully." }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - model_id must be unique (not already present).
            - brand_id must refer to an existing CarBrand.
            - All parameters required, year should be int.
        """

        # Check for required parameters
        if not all([model_id, brand_id, name, isinstance(year, int), type]):
            return { "success": False, "error": "All parameters are required, and year must be an integer." }

        if model_id in self.car_models:
            return { "success": False, "error": "Model ID already exists." }

        if brand_id not in self.car_brands:
            return { "success": False, "error": "Brand ID does not exist." }

        # Add the new car model
        self.car_models[model_id] = {
            "model_id": model_id,
            "brand_id": brand_id,
            "name": name,
            "year": year,
            "type": type
        }

        return { "success": True, "message": "Car model added successfully." }

    def update_model(
        self,
        model_id: str,
        name: str = None,
        year: int = None,
        type: str = None,
        brand_id: str = None
    ) -> dict:
        """
        Update fields for a specific CarModel by model_id.

        Args:
            model_id (str): The ID of the CarModel to update.
            name (str, optional): The new name for the car model.
            year (int, optional): The new year for the car model.
            type (str, optional): The new type for the car model.
            brand_id (str, optional): The new brand ID (must reference an existing CarBrand).

        Returns:
            dict: On success:
                {"success": True, "message": "Car model updated successfully."}
            On failure:
                {"success": False, "error": ... }

        Constraints:
            - CarModel must exist.
            - If brand_id is provided, it must reference an existing CarBrand.
            - At least one updatable field must be provided (name, year, type, brand_id).
        """
        car_model = self.car_models.get(model_id)
        if car_model is None:
            return {"success": False, "error": "Car model does not exist."}

        updatable = False
        # Check and update each field if provided.
        if name is not None:
            car_model["name"] = name
            updatable = True
        if year is not None:
            car_model["year"] = year
            updatable = True
        if type is not None:
            car_model["type"] = type
            updatable = True
        if brand_id is not None:
            if brand_id not in self.car_brands:
                return {"success": False, "error": "Brand does not exist."}
            car_model["brand_id"] = brand_id
            updatable = True

        if not updatable:
            return {"success": False, "error": "No valid fields to update provided."}

        self.car_models[model_id] = car_model
        return {"success": True, "message": "Car model updated successfully."}

    def delete_model(self, model_id: str, cascade: bool = False) -> dict:
        """
        Delete a car model from the database.

        Args:
            model_id (str): The ID of the CarModel to delete.
            cascade (bool): If True, also deletes all CarUnits associated with this model.
                            If False, deletion is not permitted if any CarUnits reference this model.

        Returns:
            dict: {
                "success": True,
                "message": str  # Confirmation of deletion
            }
            or
            {
                "success": False,
                "error": str  # Description of the error
            }

        Constraints:
            - If any CarUnits reference this CarModel and cascade is False, refuse deletion.
            - If cascade is True, remove all associated CarUnits before deleting the model.
            - If the CarModel does not exist, return error.
        """
        # Check existence
        if model_id not in self.car_models:
            return { "success": False, "error": "CarModel does not exist" }
    
        # Check for associated units
        associated_units = [unit_id for unit_id, unit in self.car_units.items() if unit["model_id"] == model_id]
    
        if associated_units:
            if not cascade:
                return {
                    "success": False,
                    "error": "Cannot delete CarModel: units exist for this model. Use cascade=True to delete all associated units."
                }
            # Delete all associated units (cascading)
            for unit_id in associated_units:
                del self.car_units[unit_id]
    
        # Delete the CarModel
        del self.car_models[model_id]
        msg = f"CarModel {model_id} deleted"
        if associated_units:
            msg += f" (plus {len(associated_units)} associated CarUnit(s))"
        return { "success": True, "message": msg }

    def add_unit(
        self,
        unit_id: str,
        model_id: str,
        VIN: str,
        availability_status: str,
        location: str
    ) -> dict:
        """
        Add a new car unit to the database, associated with a valid car model.

        Args:
            unit_id (str): Unique identifier for the car unit.
            model_id (str): Model ID (must exist in car_models).
            VIN (str): Vehicle Identification Number.
            availability_status (str): Availability of the car (e.g., 'available', 'unavailable').
            location (str): The location where the car is kept.

        Returns:
            dict: {
                "success": True,
                "message": "Car unit added."
            }
            or
            {
                "success": False,
                "error": <description>
            }

        Constraints:
            - unit_id must be unique.
            - model_id must exist in the car_models table.
        """
        if unit_id in self.car_units:
            return {"success": False, "error": "Unit ID already exists."}
        if model_id not in self.car_models:
            return {"success": False, "error": "Model ID does not exist."}
        # (Optional: Validate other fields not empty, not required by spec)

        unit_info = {
            "unit_id": unit_id,
            "model_id": model_id,
            "VIN": VIN,
            "availability_status": availability_status,
            "location": location
        }
        self.car_units[unit_id] = unit_info
        return {"success": True, "message": "Car unit added."}

    def update_unit(
        self,
        unit_id: str,
        model_id: str = None,
        VIN: str = None,
        availability_status: str = None,
        location: str = None
    ) -> dict:
        """
        Update the information of an existing car unit.

        Args:
            unit_id (str): The unique identifier for the CarUnit to update.
            model_id (str, optional): If provided, updates the CarUnit's model reference. Must exist in car_models.
            VIN (str, optional): If provided, updates the CarUnit's VIN.
            availability_status (str, optional): If provided, updates the CarUnit's availability status.
            location (str, optional): If provided, updates the CarUnit's location.

        Returns:
            dict: {
                "success": True,
                "message": "Updated car unit <unit_id>."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - CarUnit must exist.
            - If updating model_id, the model must exist in car_models.
        """
        if unit_id not in self.car_units:
            return {"success": False, "error": "CarUnit not found."}

        unit = self.car_units[unit_id]

        # Update model_id if provided
        if model_id is not None:
            if model_id not in self.car_models:
                return {"success": False, "error": "Target model_id does not exist."}
            unit["model_id"] = model_id

        # Update other fields
        if VIN is not None:
            unit["VIN"] = VIN
        if availability_status is not None:
            unit["availability_status"] = availability_status
        if location is not None:
            unit["location"] = location

        self.car_units[unit_id] = unit  # Save back (dict is reference, but explicit)

        return {
            "success": True,
            "message": f"Updated car unit {unit_id}."
        }

    def set_unit_availability(self, unit_id: str, new_status: str) -> dict:
        """
        Change the availability_status of a car unit.

        Args:
            unit_id (str): Identifier of the car unit to update.
            new_status (str): New availability status (e.g., "available", "rented", "sold").

        Returns:
            dict:
                On success: { "success": True, "message": "Availability status updated for unit <unit_id>" }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - unit_id must reference an existing CarUnit.
        """
        if unit_id not in self.car_units:
            return {"success": False, "error": f"Car unit with id '{unit_id}' does not exist."}

        self.car_units[unit_id]["availability_status"] = new_status
        return {"success": True, "message": f"Availability status updated for unit {unit_id}"}

    def delete_unit(self, unit_id: str) -> dict:
        """
        Remove a car unit from the inventory.

        Args:
            unit_id (str): The unique identifier of the car unit to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Car unit removed from inventory."
            }
            or
            {
                "success": False,
                "error": <error message>
            }

        Constraints:
            - The unit must exist in the inventory to be removed.
        """
        if unit_id not in self.car_units:
            return {
                "success": False,
                "error": f"Car unit with unit_id '{unit_id}' does not exist."
            }

        del self.car_units[unit_id]
        return {
            "success": True,
            "message": "Car unit removed from inventory."
        }

    def bulk_update_unit_availability(
        self,
        new_status: str,
        unit_ids: list[str] = None,
        model_id: str = None,
        brand_id: str = None
    ) -> dict:
        """
        Bulk update the availability_status for multiple car units.

        Args:
            new_status (str): The new value to set for availability_status.
            unit_ids (list[str], optional): List of unit_ids to update directly.
            model_id (str, optional): If specified, update all units under this model.
            brand_id (str, optional): If specified, update all units under all models of this brand.

        Returns:
            dict: {
              "success": True,
              "message": "<number> units updated"
            }
            or
            {
              "success": False,
              "error": "<error reason>"
            }

        Constraints:
            - At least one of unit_ids, model_id, brand_id must be provided.
            - Only existing units are updated.
            - model_id/brand_id must correspond to known objects.
        """
        # Validate that at least one selector is provided
        if unit_ids is None and model_id is None and brand_id is None:
            return {"success": False, "error": "No selection criteria provided (must specify unit_ids, model_id, or brand_id)"}

        # Pre-selection: start with all units
        selected_unit_ids = set()

        # If unit_ids specified, filter only existing
        if unit_ids is not None:
            for uid in unit_ids:
                if uid in self.car_units:
                    selected_unit_ids.add(uid)
            # Don't error if none exist yet; other criteria may select units

        # If model_id specified, validate and collect units
        if model_id is not None:
            if model_id not in self.car_models:
                return {"success": False, "error": "model_id does not exist"}
            for uid, unit_info in self.car_units.items():
                if unit_info["model_id"] == model_id:
                    selected_unit_ids.add(uid)

        # If brand_id specified, validate and collect matching models' units
        if brand_id is not None:
            if brand_id not in self.car_brands:
                return {"success": False, "error": "brand_id does not exist"}
            # Find all models for this brand
            model_ids_of_brand = {mid for mid, minfo in self.car_models.items() if minfo["brand_id"] == brand_id}
            for uid, unit_info in self.car_units.items():
                if unit_info["model_id"] in model_ids_of_brand:
                    selected_unit_ids.add(uid)

        if not selected_unit_ids:
            return {"success": False, "error": "No units matched the criteria"}

        updated_count = 0
        for uid in selected_unit_ids:
            self.car_units[uid]["availability_status"] = new_status
            updated_count += 1

        return {
            "success": True,
            "message": f"{updated_count} units updated"
        }


class TransportationDatabaseSystem(BaseEnv):
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

    def list_all_brands(self, **kwargs):
        return self._call_inner_tool('list_all_brands', kwargs)

    def get_brand_by_id(self, **kwargs):
        return self._call_inner_tool('get_brand_by_id', kwargs)

    def list_all_models(self, **kwargs):
        return self._call_inner_tool('list_all_models', kwargs)

    def list_models_by_brand(self, **kwargs):
        return self._call_inner_tool('list_models_by_brand', kwargs)

    def get_model_by_id(self, **kwargs):
        return self._call_inner_tool('get_model_by_id', kwargs)

    def list_all_units(self, **kwargs):
        return self._call_inner_tool('list_all_units', kwargs)

    def list_units_by_model(self, **kwargs):
        return self._call_inner_tool('list_units_by_model', kwargs)

    def list_units_by_brand(self, **kwargs):
        return self._call_inner_tool('list_units_by_brand', kwargs)

    def get_unit_by_id(self, **kwargs):
        return self._call_inner_tool('get_unit_by_id', kwargs)

    def filter_units_by_availability(self, **kwargs):
        return self._call_inner_tool('filter_units_by_availability', kwargs)

    def list_available_brands(self, **kwargs):
        return self._call_inner_tool('list_available_brands', kwargs)

    def add_brand(self, **kwargs):
        return self._call_inner_tool('add_brand', kwargs)

    def update_brand(self, **kwargs):
        return self._call_inner_tool('update_brand', kwargs)

    def delete_brand(self, **kwargs):
        return self._call_inner_tool('delete_brand', kwargs)

    def add_model(self, **kwargs):
        return self._call_inner_tool('add_model', kwargs)

    def update_model(self, **kwargs):
        return self._call_inner_tool('update_model', kwargs)

    def delete_model(self, **kwargs):
        return self._call_inner_tool('delete_model', kwargs)

    def add_unit(self, **kwargs):
        return self._call_inner_tool('add_unit', kwargs)

    def update_unit(self, **kwargs):
        return self._call_inner_tool('update_unit', kwargs)

    def set_unit_availability(self, **kwargs):
        return self._call_inner_tool('set_unit_availability', kwargs)

    def delete_unit(self, **kwargs):
        return self._call_inner_tool('delete_unit', kwargs)

    def bulk_update_unit_availability(self, **kwargs):
        return self._call_inner_tool('bulk_update_unit_availability', kwargs)

