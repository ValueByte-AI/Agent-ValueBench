# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



class FarmInfo(TypedDict):
    farm_id: str
    name: str
    location: str
    total_area: float
    available_area: float

class FieldInfo(TypedDict):
    field_id: str
    farm_id: str
    area: float
    status: str
    assigned_crop_id: str

class CropInfo(TypedDict):
    crop_id: str
    farm_id: str
    crop_type_id: str
    area_allocated: float
    planting_date: str
    planted_quantity: int
    status: str

class CropTypeInfo(TypedDict):
    crop_type_id: str
    name: str
    category: str  # e.g., flower, grain
    growth_duration: float
    typical_yield_per_hectare: float

class ActivityInfo(TypedDict):
    activity_id: str
    crop_id: str
    type: str  # e.g., planting, harvesting
    date: str
    quantity: int
    notes: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Farms: {farm_id → FarmInfo}
        self.farms: Dict[str, FarmInfo] = {}

        # Fields: {field_id → FieldInfo}
        self.fields: Dict[str, FieldInfo] = {}

        # Crops: {crop_id → CropInfo}
        self.crops: Dict[str, CropInfo] = {}

        # CropTypes: {crop_type_id → CropTypeInfo}
        self.crop_types: Dict[str, CropTypeInfo] = {}

        # Activities/Tasks: {activity_id → ActivityInfo}
        self.activities: Dict[str, ActivityInfo] = {}

        # Constraints:
        # - Total land allocated for crops on a farm cannot exceed farm's total_area.
        # - A Crop must reference an existing CropType.
        # - Planted quantities must be non-negative and not exceed agronomic or physical land constraints (if modeled).
        # - Activity records reference valid crops and activity types.

    def get_farm_by_id(self, farm_id: str) -> dict:
        """
        Retrieve complete information about a specific farm by its farm_id.

        Args:
            farm_id (str): Unique identifier of the farm.
    
        Returns:
            dict: {
                "success": True,
                "data": FarmInfo  # All fields for the specified farm
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g., "Farm does not exist"
            }

        Constraints:
            - The specified farm_id must exist in the FMIS.
        """
        if farm_id not in self.farms:
            return { "success": False, "error": "Farm does not exist" }
        return { "success": True, "data": self.farms[farm_id] }

    def list_farms(self) -> dict:
        """
        List all farms currently in the system.

        Returns:
            dict: {
                "success": True,
                "data": List[FarmInfo],  # List of all FarmInfo dictionaries (possibly empty)
            }
        """
        farms_list = list(self.farms.values())
        return {
            "success": True,
            "data": farms_list
        }

    def get_fields_by_farm_id(self, farm_id: str) -> dict:
        """
        Retrieve all fields associated with the specified farm.

        Args:
            farm_id (str): The ID of the farm whose fields to retrieve.

        Returns:
            dict:
                success (bool): True if operation succeeds, otherwise False.
                data (List[FieldInfo]): List of all FieldInfo for fields belonging to the farm (may be empty).
                error (str, optional): Error description if operation fails.

        Constraints:
            - The farm_id must reference an existing farm in the system.
        """
        if farm_id not in self.farms:
            return { "success": False, "error": "Farm not found" }

        result = [
            field_info for field_info in self.fields.values()
            if field_info["farm_id"] == farm_id
        ]

        return { "success": True, "data": result }

    def get_crop_type_by_name(self, name: str) -> dict:
        """
        Retrieve crop type info based on the crop type's name.

        Args:
            name (str): The name of the crop type to look up (case sensitive).

        Returns:
            dict:
                Success: {
                    "success": True,
                    "data": CropTypeInfo  # The crop type matching the name
                }
                Failure: {
                    "success": False,
                    "error": "No crop type with the specified name found"
                }

        Constraints:
            - Name matching is case sensitive.
            - If multiple crop types share the same name, returns the first match found.
        """
        for crop_type in self.crop_types.values():
            if crop_type['name'] == name:
                return {"success": True, "data": crop_type}

        return {"success": False, "error": "No crop type with the specified name found"}

    def list_crop_types(self) -> dict:
        """
        List all defined crop types available for farming.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[CropTypeInfo]  # List of all crop types, possibly empty if none defined.
            }
        """
        # Get all crop types
        crop_types_list = list(self.crop_types.values())
        return {
            "success": True,
            "data": crop_types_list
        }

    def get_crop_type_by_id(self, crop_type_id: str) -> dict:
        """
        Retrieve details of a specific CropType by its unique crop_type_id.

        Args:
            crop_type_id (str): The unique identifier for the CropType.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "data": CropTypeInfo  # Details of the CropType
                    }
                On failure:
                    {
                        "success": False,
                        "error": "CropType not found"
                    }
        """
        crop_type = self.crop_types.get(crop_type_id)
        if crop_type is None:
            return { "success": False, "error": "CropType not found" }
        return { "success": True, "data": crop_type }

    def list_crops_by_farm_id(self, farm_id: str) -> dict:
        """
        Get all crops registered on a farm, with their area allocation and status.

        Args:
            farm_id (str): The identifier of the farm.

        Returns:
            dict: {
                "success": True,
                "data": List[CropInfo],  # List of CropInfo dicts for crops on the farm
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. invalid farm ID
            }

        Constraints:
            - The farm_id must reference an existing farm.
        """
        if farm_id not in self.farms:
            return {"success": False, "error": "Farm ID does not exist"}

        crops = [
            crop_info for crop_info in self.crops.values()
            if crop_info["farm_id"] == farm_id
        ]
        return {"success": True, "data": crops}

    def get_crop_by_id(self, crop_id: str) -> dict:
        """
        Retrieve detailed information for a specific crop by its crop_id.

        Args:
            crop_id (str): Unique identifier of the crop.

        Returns:
            dict:
              - On success: {"success": True, "data": CropInfo}
              - On failure: {"success": False, "error": str}
        """
        crop_info = self.crops.get(crop_id)
        if not crop_info:
            return {"success": False, "error": "Crop with the given crop_id does not exist."}
        return {"success": True, "data": crop_info}

    def get_crop_area_allocation_for_farm(self, farm_id: str) -> dict:
        """
        Compute and list the total area allocated to crops for a given farm.

        Args:
            farm_id (str): The identifier of the farm.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "data": {
                        "farm_id": str,
                        "total_area_allocated": float,  # Total area allocated to crops
                        "crop_count": int,              # Number of crops included
                        "details": List[CropInfo],      # Detailed crop info
                    }
                }
                On failure:
                {
                    "success": False,
                    "error": str  # Reason, e.g. "Farm not found"
                }

        Constraints:
            - The farm must exist.
            - Will accurately sum all area_allocated entries for crops linked to this farm.
        """
        if farm_id not in self.farms:
            return { "success": False, "error": "Farm not found" }
    
        crops_on_farm = [
            crop for crop in self.crops.values()
            if crop["farm_id"] == farm_id
        ]
        total_area_allocated = sum(crop.get("area_allocated", 0.0) for crop in crops_on_farm)
    
        return {
            "success": True,
            "data": {
                "farm_id": farm_id,
                "total_area_allocated": total_area_allocated,
                "crop_count": len(crops_on_farm),
                "details": crops_on_farm
            }
        }

    def get_activities_by_crop_id(self, crop_id: str) -> dict:
        """
        Retrieve all logged activities/tasks related to a specific crop.

        Args:
            crop_id (str): The ID of the crop whose activities are to be retrieved.

        Returns:
            dict: If crop exists:
                     {
                       "success": True,
                       "data": List[ActivityInfo]   # May be empty if no activities found.
                     }
                  If crop does not exist:
                     {
                       "success": False,
                       "error": "Crop does not exist"
                     }

        Constraints:
            - crop_id must reference an existing Crop.
        """
        if crop_id not in self.crops:
            return { "success": False, "error": "Crop does not exist" }
    
        result = [
            activity for activity in self.activities.values()
            if activity['crop_id'] == crop_id
        ]
        return { "success": True, "data": result }

    def get_field_by_id(self, field_id: str) -> dict:
        """
        Retrieve a specific field’s information by its ID.

        Args:
            field_id (str): The unique identifier of the field.

        Returns:
            dict: {
                "success": True,
                "data": FieldInfo  # if the field exists
            }
            or
            {
                "success": False,
                "error": "Field not found"  # if the id does not correspond to a field
            }

        Constraints:
            - The field with given field_id must exist in the system.
        """
        field_info = self.fields.get(field_id)
        if field_info is None:
            return {"success": False, "error": "Field not found"}

        return {"success": True, "data": field_info}

    def add_crop_type(
        self,
        crop_type_id: str,
        name: str,
        category: str,
        growth_duration: float,
        typical_yield_per_hectare: float
    ) -> dict:
        """
        Create and add a new CropType to the system.

        Args:
            crop_type_id (str): Unique identifier for the new crop type.
            name (str): Name of the crop species.
            category (str): Crop category, e.g., 'flower', 'grain'.
            growth_duration (float): Time required for growth (must be non-negative).
            typical_yield_per_hectare (float): Typical yield per hectare (must be non-negative).

        Returns:
            dict: {
                "success": True,
                "message": "CropType <crop_type_id> added."
            }
            OR
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
          - crop_type_id must be unique
          - growth_duration and typical_yield_per_hectare must be non-negative
          - All parameters must be provided (not empty)
        """
        if not all([crop_type_id, name, category]):
            return {"success": False, "error": "All fields (id, name, category) must be provided and not empty."}
        if crop_type_id in self.crop_types:
            return {"success": False, "error": "CropType ID already exists."}
        if not isinstance(growth_duration, (float, int)) or growth_duration < 0:
            return {"success": False, "error": "Growth duration must be a non-negative number."}
        if not isinstance(typical_yield_per_hectare, (float, int)) or typical_yield_per_hectare < 0:
            return {"success": False, "error": "Typical yield per hectare must be a non-negative number."}

        crop_type_info: CropTypeInfo = {
            "crop_type_id": crop_type_id,
            "name": name,
            "category": category,
            "growth_duration": float(growth_duration),
            "typical_yield_per_hectare": float(typical_yield_per_hectare)
        }
        self.crop_types[crop_type_id] = crop_type_info
        return {"success": True, "message": f"CropType {crop_type_id} added."}

    def add_crop(
        self,
        crop_id: str,
        farm_id: str,
        crop_type_id: str,
        area_allocated: float,
        planting_date: str,
        planted_quantity: int,
        status: str
    ) -> dict:
        """
        Add/register a new crop on a farm, specifying crop type, area allocated, and other fields.

        Args:
            crop_id (str): Unique identifier for the crop.
            farm_id (str): ID of the farm where the crop is planted.
            crop_type_id (str): Existing crop type identifier.
            area_allocated (float): Area (in hectares, etc.) allocated to this crop (> 0).
            planting_date (str): Planting date (format not enforced here).
            planted_quantity (int): Quantity planted (must be >= 0).
            status (str): Status of the crop (e.g., "planted").

        Returns:
            dict: On success:
                {
                    "success": True,
                    "message": "Crop added",
                    "crop_info": <CropInfo>
                }
            On failure:
                {
                    "success": False,
                    "error": <reason>
                }

        Constraints:
            - crop_id must be unique
            - farm_id must exist
            - crop_type_id must exist
            - area_allocated > 0 and farm has enough available_area
            - planted_quantity >= 0
            - Total land allocated for crops on the farm cannot exceed total_area
        """

        # 1. Uniqueness of crop_id
        if crop_id in self.crops:
            return { "success": False, "error": "Crop ID already exists" }

        # 2. Farm existence
        farm = self.farms.get(farm_id)
        if farm is None:
            return { "success": False, "error": "Farm not found" }

        # 3. CropType existence
        if crop_type_id not in self.crop_types:
            return { "success": False, "error": "Crop type not found" }

        # 4. area_allocated validity
        if not isinstance(area_allocated, (float, int)) or area_allocated <= 0:
            return { "success": False, "error": "area_allocated must be a positive number" }
        if area_allocated > farm["available_area"]:
            return { 
                "success": False, 
                "error": f"Not enough available area on farm (available: {farm['available_area']}, requested: {area_allocated})"
            }
        # 5. planted_quantity validity
        if not isinstance(planted_quantity, int) or planted_quantity < 0:
            return { "success": False, "error": "planted_quantity must be a non-negative integer" }

        # Passed all checks: register the crop record.
        # Land deduction is handled explicitly by allocate_crop_area_to_farm.
        crop_info = {
            "crop_id": crop_id,
            "farm_id": farm_id,
            "crop_type_id": crop_type_id,
            "area_allocated": float(area_allocated),
            "planting_date": planting_date,
            "planted_quantity": int(planted_quantity),
            "status": status
        }
        self.crops[crop_id] = crop_info

        return { "success": True, "message": "Crop added", "crop_info": crop_info }

    def allocate_crop_area_to_farm(self, farm_id: str, area_to_allocate: float) -> dict:
        """
        Subtracts the specified area from the farm's available_area to reflect
        allocation of land to crops. Enforces land use constraints.

        Args:
            farm_id (str): ID of the farm.
            area_to_allocate (float): Area to allocate (must be > 0).

        Returns:
            dict: 
                - On success: { "success": True, "message": "Allocated X area to crops on farm <farm_id>." }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - Farm must exist.
            - area_to_allocate must be a positive number.
            - area_to_allocate cannot exceed farm's available_area.
            - Total allocated crop area on a farm must not exceed total_area (enforced by available_area logic).
        """
        farm = self.farms.get(farm_id)
        if farm is None:
            return { "success": False, "error": f"Farm with id {farm_id} does not exist." }

        if not isinstance(area_to_allocate, (int, float)) or area_to_allocate <= 0:
            return { "success": False, "error": "Area to allocate must be a positive number." }

        if area_to_allocate > farm["available_area"]:
            return { 
                "success": False, 
                "error": f"Not enough available area on farm {farm_id}: requested {area_to_allocate}, available {farm['available_area']}" 
            }

        farm["available_area"] -= area_to_allocate
        # Optional: maintain precision (no negative small floats)—set to zero if almost zero.
        if abs(farm["available_area"]) < 1e-6:
            farm["available_area"] = 0.0
        self.farms[farm_id] = farm

        return { 
            "success": True, 
            "message": f"Allocated {area_to_allocate} area to crops on farm {farm_id}."
        }

    def update_farm_available_area(self, farm_id: str, new_available_area: float) -> dict:
        """
        Directly adjust the available_area value of a specified farm.

        Args:
            farm_id (str): The identifier of the farm to update.
            new_available_area (float): The new available area value to set.

        Returns:
            dict: {
                "success": True,
                "message": "Farm available_area updated to <value> for farm <farm_id>"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Farm with farm_id must exist.
            - new_available_area >= 0.
            - new_available_area <= farm's total_area.
        """
        farm = self.farms.get(farm_id)
        if not farm:
            return { "success": False, "error": "Farm not found" }

        total_area = farm["total_area"]
        if new_available_area < 0:
            return { "success": False, "error": "Available area cannot be negative" }

        if new_available_area > total_area:
            return { "success": False, "error": "Available area cannot exceed farm's total_area" }

        # Optional: Check that sum(current crop allocations) + available_area <= total_area
        crops_for_farm = [
            crop for crop in self.crops.values()
            if crop["farm_id"] == farm_id
        ]
        allocated_area = sum(crop["area_allocated"] for crop in crops_for_farm)
        if allocated_area + new_available_area > total_area:
            return {
                "success": False,
                "error": "Sum of allocated crop area and available area exceeds farm's total_area"
            }

        farm["available_area"] = new_available_area
        self.farms[farm_id] = farm
        return {
            "success": True,
            "message": f"Farm available_area updated to {new_available_area} for farm {farm_id}"
        }

    def update_crop_planted_quantity(
        self, 
        crop_id: str, 
        quantity: int, 
        mode: str = "set"
    ) -> dict:
        """
        Set or increment the planted_quantity of a crop.

        Args:
            crop_id (str): The ID of the crop to update.
            quantity (int): The quantity to set or increment (must be non-negative).
            mode (str): 'set' to set the quantity directly, 'increment' to add to current.

        Returns:
            dict: {
                "success": True,
                "message": "Planted quantity updated for crop <crop_id>."
            }
            OR
            {
                "success": False,
                "error": "<error description>"
            }

        Constraints:
            - Crop with crop_id must exist.
            - The result planted_quantity must be non-negative.
            - quantity must be non-negative.
        """
        # Validate crop_id
        crop = self.crops.get(crop_id)
        if crop is None:
            return {"success": False, "error": f"Crop with id {crop_id} does not exist."}

        if not isinstance(quantity, int) or quantity < 0:
            return {"success": False, "error": "Quantity must be a non-negative integer."}
    
        current_quantity = crop["planted_quantity"]

        if mode == "increment":
            new_quantity = current_quantity + quantity
        else:  # "set" mode (default)
            new_quantity = quantity

        # Constraint: Planted quantities must be non-negative
        if new_quantity < 0:
            return {"success": False, "error": "Resulting planted_quantity cannot be negative."}

        crop["planted_quantity"] = new_quantity
        self.crops[crop_id] = crop  # Save update back (paranoid, for dict-style semantics)

        return {
            "success": True,
            "message": f"Planted quantity updated for crop {crop_id} (now {new_quantity})."
        }

    def add_activity(
        self,
        activity_id: str,
        crop_id: str,
        type: str,
        date: str,
        quantity: int,
        notes: str
    ) -> dict:
        """
        Log a new Activity/Task for a crop.

        Args:
            activity_id (str): Unique identifier for this activity.
            crop_id (str): The target crop this activity references.
            type (str): Activity type (e.g., planting, harvesting).
            date (str): The date of the activity.
            quantity (int): Quantity associated with the activity. Must be non-negative.
            notes (str): Notes or details about the activity.

        Returns:
            dict: {
                "success": True,
                "message": "Activity successfully added."
            }
            or
            {
                "success": False,
                "error": "Reason for failure."
            }

        Constraints:
            - activity_id must be unique.
            - crop_id must reference an existing crop.
            - quantity must be non-negative.
            - type should be a non-empty string.
        """
        # Check if activity_id already exists
        if activity_id in self.activities:
            return { "success": False, "error": "activity_id already exists" }

        # Check if crop_id exists
        if crop_id not in self.crops:
            return { "success": False, "error": "Crop does not exist" }

        # Validate type argument (at least non-empty string)
        if not isinstance(type, str) or not type.strip():
            return { "success": False, "error": "Invalid activity type" }

        # Validate quantity
        if not isinstance(quantity, int) or quantity < 0:
            return { "success": False, "error": "Quantity must be a non-negative integer" }

        # Construct ActivityInfo
        activity: ActivityInfo = {
            "activity_id": activity_id,
            "crop_id": crop_id,
            "type": type,
            "date": date,
            "quantity": quantity,
            "notes": notes
        }
        self.activities[activity_id] = activity

        return { "success": True, "message": "Activity successfully added." }

    def update_crop_status(self, crop_id: str, new_status: str) -> dict:
        """
        Change the lifecycle status of a crop (e.g., to planted, growing, harvested).

        Args:
            crop_id (str): Unique identifier of the crop.
            new_status (str): The new lifecycle status to assign.

        Returns:
            dict: 
              - {"success": True, "message": "Crop status updated." }
              - {"success": False, "error": <reason>}

        Constraints:
            - crop_id must exist.
            - No explicit restrictions on new_status value (assumed to allow any string).
        """
        if crop_id not in self.crops:
            return {"success": False, "error": "Crop not found"}
        self.crops[crop_id]['status'] = new_status
        return {"success": True, "message": "Crop status updated."}

    def modify_crop(self, crop_id: str, updates: dict) -> dict:
        """
        Edit attributes of a crop such as area_allocated or crop_type_id.
        Constraints enforced:
          - The crop must exist.
          - crop_type_id (if changed) must reference an existing CropType.
          - New area_allocated (if changed) must not push farm's total allocated crop area above its total_area.
          - area_allocated must be non-negative.
          - planted_quantity (if changed) must be non-negative.

        Args:
            crop_id (str): The crop to modify.
            updates (dict): Dictionary of fields to update and their new values.

        Returns:
            dict:
                On success: { "success": True, "message": "Crop updated successfully." }
                On failure: { "success": False, "error": "<reason>" }
        """
        if crop_id not in self.crops:
            return { "success": False, "error": "Crop does not exist." }

        crop = self.crops[crop_id]
        farm_id = crop["farm_id"]
        if farm_id not in self.farms:
            return { "success": False, "error": "Associated farm does not exist." }

        # Validate modifiable fields
        allowed_fields = {
            "crop_type_id", "area_allocated", "planting_date", "planted_quantity", "status"
        }
        unmodifiable = [k for k in updates if k not in allowed_fields]
        if unmodifiable:
            return { "success": False, "error": f"Cannot modify fields: {', '.join(unmodifiable)}" }

        # Check crop_type_id reference
        if "crop_type_id" in updates:
            new_crop_type_id = updates["crop_type_id"]
            if new_crop_type_id not in self.crop_types:
                return { "success": False, "error": f"CropType {new_crop_type_id} does not exist." }

        # Area change constraint
        if "area_allocated" in updates:
            try:
                new_area = float(updates["area_allocated"])
            except Exception:
                return { "success": False, "error": "Invalid area_allocated value." }
            if new_area < 0:
                return { "success": False, "error": "area_allocated must be non-negative." }
            # Calculate total area allocated if this crop is updated
            current_area = crop["area_allocated"]
            # Sum allocated area of all crops on this farm except this crop
            other_crops_area = sum(
                c["area_allocated"] for cid, c in self.crops.items()
                if c["farm_id"] == farm_id and cid != crop_id
            )
            farm = self.farms[farm_id]
            if other_crops_area + new_area > farm["total_area"]:
                return {
                    "success": False,
                    "error": "Total allocated crop area would exceed farm's total area."
                }

        # planted_quantity constraint
        if "planted_quantity" in updates:
            try:
                new_quantity = int(updates["planted_quantity"])
            except Exception:
                return { "success": False, "error": "Invalid planted_quantity value." }
            if new_quantity < 0:
                return { "success": False, "error": "planted_quantity must be non-negative." }

        prev_area = float(crop["area_allocated"])

        # Perform updates
        for key, value in updates.items():
            crop[key] = value

        # If area changed, adjust available_area of the farm
        if "area_allocated" in updates:
            farm = self.farms[farm_id]
            # Available area = total_area - sum(all crops' area)
            total_allocated = sum(
                c["area_allocated"] for c in self.crops.values() if c["farm_id"] == farm_id
            )
            farm["available_area"] = max(0.0, farm["total_area"] - total_allocated)
            self.farms[farm_id] = farm

        return { "success": True, "message": "Crop updated successfully." }

    def remove_crop(self, crop_id: str) -> dict:
        """
        Remove a crop from a farm and adjust the available_area accordingly.

        Args:
            crop_id (str): The ID of the crop to remove.

        Returns:
            dict:
                - success (bool): Whether the removal succeeded.
                - message (str): Success message if successful.
                - error (str, optional): Error message if failed.

        Constraints:
            - The crop must exist and reference a valid farm.
            - After crop removal, the farm's available_area is increased by the crop's area_allocated,
              but must not exceed farm's total_area.
        """
        crop = self.crops.get(crop_id)
        if not crop:
            return { "success": False, "error": "Crop not found" }
    
        farm_id = crop["farm_id"]
        farm = self.farms.get(farm_id)
        if not farm:
            return { "success": False, "error": "Referenced farm not found for this crop" }
    
        # Remove crop entry
        del self.crops[crop_id]

        # Recompute available area from the remaining crops on the farm.
        total_area = farm.get("total_area", 0.0)
        total_allocated = sum(
            remaining_crop.get("area_allocated", 0.0)
            for remaining_crop in self.crops.values()
            if remaining_crop.get("farm_id") == farm_id
        )
        farm["available_area"] = max(0.0, total_area - total_allocated)
        self.farms[farm_id] = farm

        return {
            "success": True,
            "message": f"Crop {crop_id} removed from farm {farm_id} and available area adjusted."
        }

    def update_field_assignment(self, field_id: str, crop_id: str = None) -> dict:
        """
        Assign or update the crop assigned to a specific field.

        Args:
            field_id (str): ID of the field to update.
            crop_id (str or None): ID of the crop to assign, or None to unassign crop from field.

        Returns:
            dict: {
                "success": True,
                "message": "Field assignment updated."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }
    
        Constraints:
            - The field must exist.
            - If assigning (crop_id is not None), crop must exist.
            - If assigning, crop.farm_id must match field.farm_id.
            - Updates the assigned_crop_id of the field.
        """
        # Check field existence
        if field_id not in self.fields:
            return {"success": False, "error": "Field does not exist."}
    
        field = self.fields[field_id]

        if crop_id is not None:
            # Check crop existence
            if crop_id not in self.crops:
                return {"success": False, "error": "Crop does not exist."}
            crop = self.crops[crop_id]
            # Check farm match constraint
            if crop["farm_id"] != field["farm_id"]:
                return {"success": False, "error": "Crop and field do not belong to the same farm."}
            self.fields[field_id]["assigned_crop_id"] = crop_id
            # Optionally, update 'status' to reflect assignment
            self.fields[field_id]["status"] = "assigned"
            return {"success": True, "message": f"Field {field_id} assigned to crop {crop_id}."}
        else:
            # Unassign crop
            self.fields[field_id]["assigned_crop_id"] = ""
            self.fields[field_id]["status"] = "unassigned"
            return {"success": True, "message": f"Field {field_id} crop assignment cleared."}

    def delete_activity(self, activity_id: str) -> dict:
        """
        Removes an activity/task from the activity log.

        Args:
            activity_id (str): The unique identifier for the activity to remove.

        Returns:
            dict:
                - On success:
                    { "success": True, "message": "Activity <activity_id> deleted." }
                - On error (if activity does not exist):
                    { "success": False, "error": "Activity not found." }
    
        Constraints:
            - The activity must exist in the system.
            - Removing the activity only affects the activity log; crop/task relations remain valid.
        """
        if activity_id not in self.activities:
            return { "success": False, "error": "Activity not found." }
    
        del self.activities[activity_id]
        return { "success": True, "message": f"Activity {activity_id} deleted." }

    def update_activity(
        self,
        activity_id: str,
        quantity: int = None,
        notes: str = None,
        date: str = None,
        type: str = None,
        crop_id: str = None
    ) -> dict:
        """
        Edit an existing Activity's details such as quantity, notes, type, date, or crop reference.

        Args:
            activity_id (str): Unique identifier for the activity to update.
            quantity (int, optional): New quantity for the activity (must be non-negative if given).
            notes (str, optional): New notes to associate with the activity.
            date (str, optional): New date for the activity.
            type (str, optional): New activity type (e.g., planting, harvesting).
            crop_id (str, optional): Update crop reference (must reference a valid crop).

        Returns:
            dict: {
                "success": True,
                "message": f"Activity {activity_id} updated."
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
        - The activity_id must exist.
        - If quantity is given, it must be non-negative.
        - If crop_id is given, it must exist in the current crops.
        - All provided updates are performed in-place.
        """
        if activity_id not in self.activities:
            return { "success": False, "error": "Activity does not exist" }

        activity = self.activities[activity_id]

        # Crop ID update
        if crop_id is not None:
            if crop_id not in self.crops:
                return { "success": False, "error": f"Crop {crop_id} does not exist" }
            activity["crop_id"] = crop_id

        # Type update (optional extra logic: in full FMIS may check accepted types)
        if type is not None:
            activity["type"] = type

        # Date update
        if date is not None:
            activity["date"] = date

        # Quantity update
        if quantity is not None:
            if quantity < 0:
                return { "success": False, "error": "Quantity must be non-negative" }
            activity["quantity"] = quantity

        # Notes update
        if notes is not None:
            activity["notes"] = notes

        return { "success": True, "message": f"Activity {activity_id} updated." }


class FarmManagementInformationSystem(BaseEnv):
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

    def get_farm_by_id(self, **kwargs):
        return self._call_inner_tool('get_farm_by_id', kwargs)

    def list_farms(self, **kwargs):
        return self._call_inner_tool('list_farms', kwargs)

    def get_fields_by_farm_id(self, **kwargs):
        return self._call_inner_tool('get_fields_by_farm_id', kwargs)

    def get_crop_type_by_name(self, **kwargs):
        return self._call_inner_tool('get_crop_type_by_name', kwargs)

    def list_crop_types(self, **kwargs):
        return self._call_inner_tool('list_crop_types', kwargs)

    def get_crop_type_by_id(self, **kwargs):
        return self._call_inner_tool('get_crop_type_by_id', kwargs)

    def list_crops_by_farm_id(self, **kwargs):
        return self._call_inner_tool('list_crops_by_farm_id', kwargs)

    def get_crop_by_id(self, **kwargs):
        return self._call_inner_tool('get_crop_by_id', kwargs)

    def get_crop_area_allocation_for_farm(self, **kwargs):
        return self._call_inner_tool('get_crop_area_allocation_for_farm', kwargs)

    def get_activities_by_crop_id(self, **kwargs):
        return self._call_inner_tool('get_activities_by_crop_id', kwargs)

    def get_field_by_id(self, **kwargs):
        return self._call_inner_tool('get_field_by_id', kwargs)

    def add_crop_type(self, **kwargs):
        return self._call_inner_tool('add_crop_type', kwargs)

    def add_crop(self, **kwargs):
        return self._call_inner_tool('add_crop', kwargs)

    def allocate_crop_area_to_farm(self, **kwargs):
        return self._call_inner_tool('allocate_crop_area_to_farm', kwargs)

    def update_farm_available_area(self, **kwargs):
        return self._call_inner_tool('update_farm_available_area', kwargs)

    def update_crop_planted_quantity(self, **kwargs):
        return self._call_inner_tool('update_crop_planted_quantity', kwargs)

    def add_activity(self, **kwargs):
        return self._call_inner_tool('add_activity', kwargs)

    def update_crop_status(self, **kwargs):
        return self._call_inner_tool('update_crop_status', kwargs)

    def modify_crop(self, **kwargs):
        return self._call_inner_tool('modify_crop', kwargs)

    def remove_crop(self, **kwargs):
        return self._call_inner_tool('remove_crop', kwargs)

    def update_field_assignment(self, **kwargs):
        return self._call_inner_tool('update_field_assignment', kwargs)

    def delete_activity(self, **kwargs):
        return self._call_inner_tool('delete_activity', kwargs)

    def update_activity(self, **kwargs):
        return self._call_inner_tool('update_activity', kwargs)
