# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict, Optional



class BrandInfo(TypedDict):
    brand_id: str      # Unique identifier for brand
    brand_name: str    # Unique name for brand
    country_of_origin: str

class SpecificationInfo(TypedDict):
    model_id: str
    processor: str
    ram: int              # in GB
    storage: int          # in GB
    display_size: float   # in inches
    battery_capacity: int # in mAh
    camera_specs: str
    os: str
    connectivity: str
    other_features: str

class ModelInfo(TypedDict):
    model_id: str
    brand_id: str
    model_name: str
    release_date: str      # Suggest ISO date string
    specification: SpecificationInfo

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Mobile device catalog storing brands, models, and specifications.
        """

        # Brands: {brand_id: BrandInfo}
        # State Space: Brand (brand_id, brand_name (unique), country_of_origin)
        self.brands: Dict[str, BrandInfo] = {}

        # Models: {model_id: ModelInfo}
        # State Space: Model (model_id, brand_id (must exist in brands), model_name (unique within brand),
        # release_date, specification)
        self.models: Dict[str, ModelInfo] = {}
        
        # Constraints:
        # - Each model must be linked to a valid brand via brand_id.
        # - brand_name values must be unique.
        # - model_name values must be unique within each brand.

    def list_all_brands(self) -> dict:
        """
        Retrieve the complete list of unique brands available in the database.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[BrandInfo]  # List of all brands as dictionaries (can be empty if no brands exist)
            }
        """
        return {
            "success": True,
            "data": list(self.brands.values())
        }

    def get_brand_by_name(self, brand_name: str) -> dict:
        """
        Retrieve details of a brand (brand_id, brand_name, country_of_origin) given its unique brand_name.

        Args:
            brand_name (str): The unique name of the brand to retrieve.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": BrandInfo
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Brand not found"
                    }

        Constraints:
            - brand_name must be unique in the catalog.
            - Returns information only if an exact match is found.
        """
        for brand in self.brands.values():
            if brand["brand_name"] == brand_name:
                return { "success": True, "data": brand }
        return { "success": False, "error": "Brand not found" }

    def get_brand_by_id(self, brand_id: str) -> dict:
        """
        Retrieve details of a brand using its brand_id.

        Args:
            brand_id (str): The unique identifier of the brand to look up.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": BrandInfo  # Information about the brand
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Brand not found"
                    }

        Constraints:
            - brand_id must exist in the catalog.
        """
        brand = self.brands.get(brand_id)
        if brand is None:
            return { "success": False, "error": "Brand not found" }
        return { "success": True, "data": brand }

    def list_models_by_brand_id(self, brand_id: str) -> dict:
        """
        List all models associated with a given brand_id.

        Args:
            brand_id (str): The unique identifier of the brand.

        Returns:
            dict: {
                "success": True,
                "data": List[ModelInfo]  # All models associated with the brand (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # e.g., "Brand not found"
            }

        Constraints:
            - brand_id must exist in self.brands, otherwise return error.
            - If brand exists but has no models, return success with empty list.
        """
        if brand_id not in self.brands:
            return { "success": False, "error": "Brand not found" }

        data = [
            model_info for model_info in self.models.values()
            if model_info["brand_id"] == brand_id
        ]
        return { "success": True, "data": data }

    def list_models_by_brand_name(self, brand_name: str) -> dict:
        """
        List all models offered by a brand, identified uniquely by brand_name.
        Internally looks up the corresponding brand_id.

        Args:
            brand_name (str): The unique name of the brand.

        Returns:
            dict:
                - On success:
                    { "success": True, "data": List[ModelInfo] }
                      (Empty list if the brand exists but has no models)
                - On failure:
                    { "success": False, "error": "Brand not found" }

        Constraints:
            - brand_name must be unique.
        """
        # Look up the brand_id for the given brand_name
        brand_id = None
        for b in self.brands.values():
            if b["brand_name"] == brand_name:
                brand_id = b["brand_id"]
                break

        if brand_id is None:
            return { "success": False, "error": "Brand not found" }

        models = [
            model for model in self.models.values()
            if model["brand_id"] == brand_id
        ]

        return { "success": True, "data": models }

    def get_model_by_id(self, model_id: str) -> dict:
        """
        Retrieve the full information (including embedded specification) for the model with the given model_id.

        Args:
            model_id (str): Unique identifier for the model.

        Returns:
            dict: 
                { "success": True, "data": ModelInfo }
                or
                { "success": False, "error": "Model not found" }

        Constraints:
            - model_id must exist in the catalog.
        """
        model_info = self.models.get(model_id)
        if model_info is None:
            return { "success": False, "error": "Model not found" }
        return { "success": True, "data": model_info }

    def get_model_specification(self, model_id: str) -> dict:
        """
        Retrieve the technical specification details for a particular model.

        Args:
            model_id (str): The unique identifier for the mobile device model.

        Returns:
            dict: 
                - On success: { "success": True, "data": SpecificationInfo }
                - On error:   { "success": False, "error": str }

        Constraints:
            - model_id must exist in the database.
        """
        model = self.models.get(model_id)
        if not model:
            return { "success": False, "error": "Model does not exist" }
    
        specification = model.get('specification')
        return { "success": True, "data": specification }

    def search_models_by_name(self, query: str) -> dict:
        """
        Search and return a list of models whose model_name contains the provided query string
        (case-insensitive substring match), across all brands.

        Args:
            query (str): Substring to search for in model_name.

        Returns:
            dict: {
                "success": True,
                "data": List[ModelInfo],  # List of matching models (may be empty)
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The query must be a non-empty string.
        """
        if not isinstance(query, str) or not query.strip():
            return {"success": False, "error": "Query string must be a non-empty string."}
        query_lower = query.lower()
        result = [
            model_info
            for model_info in self.models.values()
            if query_lower in model_info["model_name"].lower()
        ]
        return {"success": True, "data": result}

    def add_brand(self, brand_id: str, brand_name: str, country_of_origin: str) -> dict:
        """
        Add a new brand to the database.

        Args:
            brand_id (str): Unique identifier for the brand.
            brand_name (str): Unique name for the brand.
            country_of_origin (str): Country where the brand originates.

        Returns:
            dict: {
                "success": True,
                "message": "Brand added successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - brand_id and brand_name must not already exist in the catalog.
            - brand_name values must be unique.
            - brand_id values must be unique.
        """
        # Empty/None input validation
        if not brand_id or not brand_name or not country_of_origin:
            return { "success": False, "error": "All fields are required." }

        # Check for brand_id uniqueness
        if brand_id in self.brands:
            return { "success": False, "error": "brand_id already exists." }
    
        # Check for brand_name uniqueness
        if any(bi["brand_name"].lower() == brand_name.lower() for bi in self.brands.values()):
            return { "success": False, "error": "brand_name already exists." }

        # Insert new brand
        new_brand: BrandInfo = {
            "brand_id": brand_id,
            "brand_name": brand_name,
            "country_of_origin": country_of_origin
        }
        self.brands[brand_id] = new_brand
        return { "success": True, "message": "Brand added successfully." }

    def update_brand(
        self,
        brand_id: str,
        brand_name: str = None,
        country_of_origin: str = None
    ) -> dict:
        """
        Modify attributes for an existing brand.

        Args:
            brand_id (str): Identifier of the brand to update.
            brand_name (str, optional): New brand name. Must be unique if specified.
            country_of_origin (str, optional): New country of origin.

        Returns:
            dict: On success {"success": True, "message": ...}
                  On failure {"success": False, "error": ...}

        Constraints:
            - Brand with brand_id must exist.
            - If brand_name is updated, it must be unique (case-sensitive).
        """
        # Check if brand exists
        if brand_id not in self.brands:
            return {"success": False, "error": "Brand does not exist"}

        # Collect the brand info
        brand = self.brands[brand_id]

        # If updating brand_name, check for uniqueness
        if brand_name is not None and brand_name != brand["brand_name"]:
            if any(
                b["brand_name"] == brand_name and b_id != brand_id
                for b_id, b in self.brands.items()
            ):
                return {"success": False, "error": "Brand name already exists"}
            brand["brand_name"] = brand_name

        # Update country_of_origin if provided
        if country_of_origin is not None:
            brand["country_of_origin"] = country_of_origin

        # Optionally, if no update fields were provided, treat as no-op
        if brand_name is None and country_of_origin is None:
            return {"success": False, "error": "No update fields provided"}

        # Save back (dicts are by ref, but for clarity)
        self.brands[brand_id] = brand

        return {"success": True, "message": "Brand updated successfully"}

    def delete_brand(self, brand_id: str) -> dict:
        """
        Remove a brand from the database if no models are linked to it.

        Args:
            brand_id (str): Unique identifier for the brand to be removed.

        Returns:
            dict: {
                "success": True,
                "message": f"Brand {brand_id} deleted."
            }
            or
            {
                "success": False,
                "error": "Reason for failure"
            }

        Constraints:
            - Cannot delete a brand that is referenced by any model (referential integrity).
        """
        if brand_id not in self.brands:
            return { "success": False, "error": "Brand not found." }

        for model in self.models.values():
            if model["brand_id"] == brand_id:
                return {
                    "success": False,
                    "error": "Cannot delete brand: models still reference this brand."
                }

        del self.brands[brand_id]
        return { "success": True, "message": f"Brand {brand_id} deleted." }

    def add_model(
        self,
        model_id: str,
        brand_id: str,
        model_name: str,
        release_date: str,
        specification: SpecificationInfo
    ) -> dict:
        """
        Add a new mobile device model under a given brand.

        Args:
            model_id (str): Unique identifier for this model (must not already exist).
            brand_id (str): Existing brand to associate with this model.
            model_name (str): Model name, must be unique within this brand.
            release_date (str): Release date (ISO format suggested).
            specification (SpecificationInfo): Technical specs for this model.

        Returns:
            dict: Success or failure with an explanation.

        Constraints:
            - brand_id must exist in self.brands.
            - model_id must be unique (not already in self.models).
            - model_name must be unique *within* the brand_id.
        """
        if brand_id not in self.brands:
            return {"success": False, "error": "Brand does not exist."}

        if model_id in self.models:
            return {"success": False, "error": "Model ID already exists."}

        for m in self.models.values():
            if m["brand_id"] == brand_id and m["model_name"].lower() == model_name.lower():
                return {"success": False, "error": "Model name already exists for this brand."}

        # Optionally validate the specification's model_id matches
        if specification.get("model_id") != model_id:
            return {"success": False, "error": "Specification model_id does not match model_id."}

        # Add the model
        self.models[model_id] = {
            "model_id": model_id,
            "brand_id": brand_id,
            "model_name": model_name,
            "release_date": release_date,
            "specification": specification
        }
        return {"success": True, "message": "Model added."}

    def update_model(
        self,
        model_id: str,
        model_name: str = None,
        release_date: str = None
    ) -> dict:
        """
        Modify model information such as model_name or release_date.

        Args:
            model_id (str): Unique ID of the model to modify.
            model_name (Optional[str]): New model name. Must be unique within the brand (if provided).
            release_date (Optional[str]): New release date (ISO string). If provided, will be updated.

        Returns:
            dict: {
                "success": True,
                "message": "Model updated successfully."
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - model_id must exist.
            - If `model_name` is provided, it must be unique within the brand.
            - At least one updatable field must be provided.
        """
        # Check model exists
        if model_id not in self.models:
            return {"success": False, "error": "Model does not exist."}

        # Check at least one field to update
        if model_name is None and release_date is None:
            return {"success": False, "error": "No fields provided to update."}

        model_info = self.models[model_id]
        brand_id = model_info["brand_id"]

        # Check model_name uniqueness within brand (if updating)
        if model_name is not None:
            for other_model in self.models.values():
                if (
                    other_model["brand_id"] == brand_id and
                    other_model["model_id"] != model_id and
                    other_model["model_name"].lower() == model_name.lower()
                ):
                    return {"success": False, "error": "Model name already exists for this brand."}
            model_info["model_name"] = model_name

        if release_date is not None:
            model_info["release_date"] = release_date

        # Commit changes
        self.models[model_id] = model_info

        return {"success": True, "message": "Model updated successfully."}

    def delete_model(self, model_id: str) -> dict:
        """
        Delete a model from the database.

        Args:
            model_id (str): The unique identifier of the model to delete.

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "message": "Model <model_name> (ID: <model_id>) deleted successfully."
                }
                On failure: {
                    "success": False,
                    "error": "Model with the given ID does not exist."
                }

        Constraints:
            - The model to delete must exist in the database.
            - Removing the model also removes its specification, as this is embedded.
        """
        if model_id not in self.models:
            return { "success": False, "error": "Model with the given ID does not exist." }
    
        model_name = self.models[model_id]['model_name']
        del self.models[model_id]

        return {
            "success": True,
            "message": f"Model {model_name} (ID: {model_id}) deleted successfully."
        }

    def update_model_specification(self, model_id: str, updated_specification: dict) -> dict:
        """
        Modify the technical specification details for a particular model.
    
        Args:
            model_id (str): The unique identifier of the model to update.
            updated_specification (dict): The updated specification fields (should match SpecificationInfo keys).
    
        Returns:
            dict: 
                - On success: {"success": True, "message": "..."}
                - On failure: {"success": False, "error": "..."}
    
        Constraints:
            - The target model_id must exist.
            - Only valid specification fields (from SpecificationInfo) may be updated.
            - Partial updates are supported; only provided fields are updated.
        """
        if model_id not in self.models:
            return { "success": False, "error": "Model not found." }
    
        valid_spec_keys = {
            "model_id", "processor", "ram", "storage", "display_size",
            "battery_capacity", "camera_specs", "os", "connectivity", "other_features"
        }
        model = self.models[model_id]

        for k, v in updated_specification.items():
            if k in valid_spec_keys:
                model['specification'][k] = v
        # Ensure the model_id in specification always matches parent model_id
        model['specification']['model_id'] = model_id

        return { "success": True, "message": f"Specification for model {model_id} updated successfully." }


class MobileDeviceCatalogDatabase(BaseEnv):
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

    def get_brand_by_name(self, **kwargs):
        return self._call_inner_tool('get_brand_by_name', kwargs)

    def get_brand_by_id(self, **kwargs):
        return self._call_inner_tool('get_brand_by_id', kwargs)

    def list_models_by_brand_id(self, **kwargs):
        return self._call_inner_tool('list_models_by_brand_id', kwargs)

    def list_models_by_brand_name(self, **kwargs):
        return self._call_inner_tool('list_models_by_brand_name', kwargs)

    def get_model_by_id(self, **kwargs):
        return self._call_inner_tool('get_model_by_id', kwargs)

    def get_model_specification(self, **kwargs):
        return self._call_inner_tool('get_model_specification', kwargs)

    def search_models_by_name(self, **kwargs):
        return self._call_inner_tool('search_models_by_name', kwargs)

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

    def update_model_specification(self, **kwargs):
        return self._call_inner_tool('update_model_specification', kwargs)

