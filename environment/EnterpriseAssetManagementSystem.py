# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict



# ---- Entity Definitions ----

class AssetInfo(TypedDict):
    asset_id: str
    asset_type: str
    name: str
    status: str
    owner_id: str
    documentation_link: str

class DigitalAssetVersionInfo(TypedDict):
    version: str
    label: str
    url: str

class DigitalAssetInfo(TypedDict):
    asset_id: str
    software_name: str
    available_versions: List[DigitalAssetVersionInfo]
    license_info: str

class PhysicalAssetInfo(TypedDict):
    asset_id: str
    category: str
    make: str
    model: str
    year: int
    identification_number: str
    origin_country: str

class VehicleInfo(TypedDict):
    asset_id: str
    license_plate: str
    make: str
    model: str
    year: int
    origin_country: str

class OwnerInfo(TypedDict):
    owner_id: str
    name: str
    contact_info: str
    owner_type: str

# ---- Environment Class ----

class _GeneratedEnvImpl:
    def __init__(self):
        # Asset: {asset_id: AssetInfo}
        self.assets: Dict[str, AssetInfo] = {}

        # DigitalAsset: {asset_id: DigitalAssetInfo}
        self.digital_assets: Dict[str, DigitalAssetInfo] = {}

        # PhysicalAsset: {asset_id: PhysicalAssetInfo}
        self.physical_assets: Dict[str, PhysicalAssetInfo] = {}

        # Vehicle: {asset_id: VehicleInfo}
        self.vehicles: Dict[str, VehicleInfo] = {}

        # Owner (User/Department): {owner_id: OwnerInfo}
        self.owners: Dict[str, OwnerInfo] = {}

        # Constraints (see below for enforcement in logic):
        # - Each asset must have a unique asset_id.
        # - Certain asset types (like vehicles) require specific attributes (e.g., license_plate).
        # - Digital asset versions must include version, label, and URL.
        # - Asset ownership must be assignable to a user or department.
        # - Status of an asset must be kept up to date (e.g., active, decommissioned).
        # - Documentation links must be accessible for compliance and auditing.

    def get_digital_asset_by_software_name(self, software_name: str) -> dict:
        """
        Retrieve information for a digital asset by its software name.

        Args:
            software_name (str): The name of the digital asset software to search for.

        Returns:
            dict:
                success: True and 'data' with DigitalAssetInfo if found,
                else success: False with an error message.

        Constraints:
            - Returns the first asset matching the software name (case-sensitive).
            - Digital asset must exist with the specified software name.
        """
        for asset in self.digital_assets.values():
            if asset.get("software_name") == software_name:
                return {"success": True, "data": asset}
        return {
            "success": False,
            "error": f"No digital asset found with software name: {software_name}"
        }

    def list_digital_asset_versions(self, asset_id: str = None, software_name: str = None) -> dict:
        """
        List all available versions (with version, label, and URL) for a given digital asset.

        Args:
            asset_id (str, optional): The unique asset ID of the digital asset.
            software_name (str, optional): The software name of the digital asset.

        Returns:
            dict: 
                If successful:
                    {
                        "success": True,
                        "data": List[DigitalAssetVersionInfo]  # Each with version, label, url
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason for failure (missing identifier, asset not found)
                    }

        Constraints:
            - At least one of asset_id or software_name must be provided.
            - The asset must exist in the digital_assets dictionary.
        """
        if not asset_id and not software_name:
            return {
                "success": False,
                "error": "Must provide either asset_id or software_name to identify digital asset."
            }

        digital_asset = None
        if asset_id:
            digital_asset = self.digital_assets.get(asset_id)
        elif software_name:
            # Search for the first matching digital asset by software_name
            for asset in self.digital_assets.values():
                if asset.get("software_name") == software_name:
                    digital_asset = asset
                    break

        if not digital_asset:
            return {
                "success": False,
                "error": "Digital asset not found with the specified identifier."
            }
    
        versions = digital_asset.get("available_versions", [])
        return {
            "success": True,
            "data": versions
        }

    def get_asset_by_id(self, asset_id: str) -> dict:
        """
        Retrieve basic asset information by asset_id.

        Args:
            asset_id (str): Unique identifier of the asset.

        Returns:
            dict: {
                "success": True,
                "data": AssetInfo  # Dictionary containing asset_id, asset_type, name, status, owner_id, documentation_link
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g., asset not found
            }

        Constraints:
            - Asset must exist in the system with the given asset_id.
        """
        asset_info = self.assets.get(asset_id)
        if asset_info is None:
            return { "success": False, "error": "Asset not found" }
        return { "success": True, "data": asset_info }

    def get_vehicle_by_license_plate(self, license_plate: str) -> dict:
        """
        Retrieve detailed vehicle information by its license plate.

        Args:
            license_plate (str): The license plate identifier of the vehicle.

        Returns:
            dict: {
                "success": True,
                "data": VehicleInfo (dict with keys: asset_id, license_plate, make, model, year, origin_country)
            }
            or
            {
                "success": False,
                "error": str  # "Vehicle not found for the given license plate"
            }

        Constraints:
            - The license plate must exist in exactly one vehicle entity.
        """
        for vehicle in self.vehicles.values():
            if vehicle.get("license_plate") == license_plate:
                return {"success": True, "data": vehicle}
        return {"success": False, "error": "Vehicle not found for the given license plate"}

    def get_physical_asset_by_id(self, asset_id: str) -> dict:
        """
        Retrieve detailed physical asset information given its asset_id.

        Args:
            asset_id (str): The unique identifier of the physical asset.

        Returns:
            dict: {
                "success": True,
                "data": PhysicalAssetInfo  # if asset found
            }
            or
            {
                "success": False,
                "error": str  # if physical asset is not found
            }

        Constraints:
            - asset_id must exist in physical_assets.
        """
        if asset_id not in self.physical_assets:
            return { "success": False, "error": "Physical asset not found" }
        asset_info = self.physical_assets[asset_id]
        return { "success": True, "data": asset_info }

    def list_assets_by_owner(self, owner_id: str) -> dict:
        """
        List all assets assigned to a specific owner.

        Args:
            owner_id (str): The owner_id of the user or department.

        Returns:
            dict:
                - If the owner exists:
                    { "success": True, "data": List[AssetInfo] }
                - If the owner does not exist:
                    { "success": False, "error": "Owner does not exist" }

        Constraints:
            - owner_id must exist in the system.
            - Returns all AssetInfo dicts (empty list if owner has no assets).
        """
        if owner_id not in self.owners:
            return { "success": False, "error": "Owner does not exist" }

        results = [
            asset for asset in self.assets.values()
            if asset["owner_id"] == owner_id
        ]
        return { "success": True, "data": results }

    def get_owner_info(self, owner_id: str = None, name: str = None) -> dict:
        """
        Retrieve owner (user or department) information by owner_id and/or name.

        Args:
            owner_id (str, optional): The unique ID of the owner.
            name (str, optional): The name of the owner.

        Returns:
            dict:
                On success: { "success": True, "data": [OwnerInfo, ...] }  # Data is a list of owner info dicts (possibly empty)
                On error (e.g., no parameters): { "success": False, "error": str }
        Constraints:
            - At least one of owner_id or name must be provided.
            - If both are provided, only return owner(s) that match both.
        """
        if not owner_id and not name:
            return { "success": False, "error": "At least one of owner_id or name must be provided" }

        result = []
        if owner_id and name:
            # Both supplied: only exact match
            info = self.owners.get(owner_id)
            if info and info.get("name") == name:
                result.append(info)
        elif owner_id:
            info = self.owners.get(owner_id)
            if info:
                result.append(info)
        elif name:
            # Search for all owners with matching name
            for oinfo in self.owners.values():
                if oinfo.get("name") == name:
                    result.append(oinfo)

        return { "success": True, "data": result }

    def list_assets_by_type(self, asset_type: str) -> dict:
        """
        Retrieve all assets of a specified asset_type.

        Args:
            asset_type (str): The type of assets to retrieve (e.g., 'vehicle', 'equipment', 'digital_asset').

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": List[AssetInfo]  # Possibly empty list if no assets of given type
                    }
                - On error (invalid input):
                    {
                        "success": False,
                        "error": str
                    }
        Constraints:
            - asset_type must be a non-empty string.
        """
        if not isinstance(asset_type, str) or not asset_type.strip():
            return {
                "success": False,
                "error": "asset_type must be a non-empty string"
            }
        filtered_assets = [
            asset_info for asset_info in self.assets.values()
            if asset_info.get("asset_type", "").lower() == asset_type.lower()
        ]
        return {
            "success": True,
            "data": filtered_assets
        }

    def check_asset_status(self, asset_id: str) -> dict:
        """
        Query the current status (e.g., active, decommissioned) of an asset by asset_id.

        Args:
            asset_id (str): The unique identifier of the asset.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "asset_id": str,
                    "status": str
                }
            }
            or
            {
                "success": False,
                "error": str  # "Asset not found"
            }

        Constraints:
            - The asset_id must exist in the system.
        """
        asset = self.assets.get(asset_id)
        if asset is None:
            return {"success": False, "error": "Asset not found"}
        return {
            "success": True,
            "data": {
                "asset_id": asset_id,
                "status": asset["status"],
            }
        }

    def get_asset_documentation_link(self, asset_id: str) -> dict:
        """
        Retrieve a given asset's documentation link for compliance/auditing.

        Args:
            asset_id (str): The unique identifier for the asset.

        Returns:
            dict: {
                "success": True,
                "data": str  # The documentation link for the asset (may be empty if not set)
            }
            OR
            {
                "success": False,
                "error": str  # Reason (asset not found)
            }
        Constraints:
            - asset_id must exist in the system.
        """
        asset = self.assets.get(asset_id)
        if asset is None:
            return { "success": False, "error": "Asset with given asset_id does not exist." }
    
        return { "success": True, "data": asset.get("documentation_link", "") }

    def validate_digital_asset_versions_structure(self) -> dict:
        """
        Ensures every available_versions entry in each digital asset has
        the required fields: 'version', 'label', and 'url'.

        Returns:
            dict: {
                "success": True,
                "data": List[dict], # Each dict contains {'asset_id': str, 'problems': List[str]}
                    # (empty list if all conform)
            }

        Constraints:
            - Each asset in self.digital_assets' available_versions must be a list,
              each element a dict with keys 'version', 'label', 'url'.
        """
        problems = []
        for asset_id, asset_info in self.digital_assets.items():
            asset_problems = []
            versions = asset_info.get("available_versions")
            if not isinstance(versions, list):
                asset_problems.append("available_versions is not a list")
            else:
                for idx, version_entry in enumerate(versions):
                    missing_keys = [k for k in ["version", "label", "url"] if k not in version_entry]
                    if missing_keys:
                        asset_problems.append(
                            f"Version {idx} missing keys: {', '.join(missing_keys)}"
                        )
                    # Optionally, check that all keys are strings:
                    for k in ["version", "label", "url"]:
                        if k in version_entry and not isinstance(version_entry[k], str):
                            asset_problems.append(
                                f"Version {idx} '{k}' is not a string"
                            )
            if asset_problems:
                problems.append({
                    "asset_id": asset_id,
                    "problems": asset_problems
                })
        return { "success": True, "data": problems }

    def add_new_asset(self, asset_info: dict, extra_info: dict = None) -> dict:
        """
        Add (register) a new asset (physical or digital) with all required attributes, ensuring unique asset_id.

        Args:
            asset_info (dict): AssetInfo fields:
                asset_id, asset_type, name, status, owner_id, documentation_link.
            extra_info (dict, optional): Additional info needed depending on asset_type:
                - For 'digital': {software_name, available_versions (list), license_info}
                - For 'physical': {category, make, model, year, identification_number, origin_country}
                - For 'vehicle': {license_plate, make, model, year, origin_country}

        Returns:
            dict: {
                "success": True,
                "message": "Asset <asset_id> registered successfully."
            }
            OR
            dict: {
                "success": False,
                "error": "<Error reason>"
            }

        Constraints:
            - asset_id must be globally unique.
            - owner_id must exist.
            - Asset specific constraints enforced (see logic).
        """
        if not isinstance(asset_info, dict):
            return {"success": False, "error": "asset_info must be a dict"}

        asset_id = asset_info.get("asset_id")
        asset_type = asset_info.get("asset_type")
        owner_id = asset_info.get("owner_id")
        documentation_link = asset_info.get("documentation_link")
        name = asset_info.get("name")
        status = asset_info.get("status")

        # Check for required AssetInfo fields
        required_asset_fields = ["asset_id", "asset_type", "name", "status", "owner_id", "documentation_link"]
        for f in required_asset_fields:
            if asset_info.get(f) is None or (isinstance(asset_info[f], str) and asset_info[f].strip() == ""):
                return {"success": False, "error": f"Missing required field: {f}"}

        # Check asset_id uniqueness
        if (asset_id in self.assets or
            asset_id in self.digital_assets or
            asset_id in self.physical_assets or
            asset_id in self.vehicles):
            return {"success": False, "error": f"Asset with asset_id '{asset_id}' already exists."}

        # Owner must exist
        if owner_id not in self.owners:
            return {"success": False, "error": f"Owner '{owner_id}' does not exist."}

        # Documentation link should be non-empty
        if not documentation_link or not isinstance(documentation_link, str):
            return {"success": False, "error": "Invalid or missing documentation_link."}

        normalized_asset_type = asset_type.lower()
        if normalized_asset_type not in {"digital", "physical", "vehicle"}:
            return {"success": False, "error": f"Unknown asset_type '{asset_type}'. Must be 'physical', 'digital', or 'vehicle'."}

        # Register common asset info
        self.assets[asset_id] = {
            "asset_id": asset_id,
            "asset_type": asset_type,
            "name": name,
            "status": status,
            "owner_id": owner_id,
            "documentation_link": documentation_link,
        }

        # Asset type-specific registration
        if normalized_asset_type == "digital":
            if not extra_info or not isinstance(extra_info, dict):
                return {"success": False, "error": "extra_info required for digital assets."}
            software_name = extra_info.get("software_name")
            available_versions = extra_info.get("available_versions")
            license_info = extra_info.get("license_info")

            if not all([software_name, available_versions, license_info]):
                return {"success": False, "error": "Missing digital asset info (software_name, available_versions, license_info required)."}

            # Validate available_versions structure
            if not isinstance(available_versions, list) or len(available_versions) == 0:
                return {"success": False, "error": "available_versions must be a non-empty list."}
            for idx, v in enumerate(available_versions):
                if not (isinstance(v, dict) and "version" in v and "label" in v and "url" in v):
                    return {"success": False, "error": f"available_versions[{idx}] missing required fields."}

            self.digital_assets[asset_id] = {
                "asset_id": asset_id,
                "software_name": software_name,
                "available_versions": available_versions,
                "license_info": license_info,
            }

        elif normalized_asset_type == "vehicle":
            # A vehicle is a kind of physical asset, add to both
            if not extra_info or not isinstance(extra_info, dict):
                return {"success": False, "error": "extra_info required for vehicle assets."}
            required_vehicle_fields = ["license_plate", "make", "model", "year", "origin_country"]
            for f in required_vehicle_fields:
                if extra_info.get(f) in [None, ""]:
                    return {"success": False, "error": f"Missing required vehicle field: {f}"}

            license_plate = extra_info["license_plate"]
            make = extra_info["make"]
            model = extra_info["model"]
            year = extra_info["year"]
            origin_country = extra_info["origin_country"]

            # Also require identification_number and category for the physical asset record
            identification_number = extra_info.get("identification_number", f"{license_plate}-{asset_id}")
            category = extra_info.get("category", "vehicle")

            # Add to physical_assets
            self.physical_assets[asset_id] = {
                "asset_id": asset_id,
                "category": category,
                "make": make,
                "model": model,
                "year": year,
                "identification_number": identification_number,
                "origin_country": origin_country,
            }
            # Add to vehicles
            self.vehicles[asset_id] = {
                "asset_id": asset_id,
                "license_plate": license_plate,
                "make": make,
                "model": model,
                "year": year,
                "origin_country": origin_country,
            }

        elif normalized_asset_type == "physical":
            if not extra_info or not isinstance(extra_info, dict):
                return {"success": False, "error": "extra_info required for physical assets."}
            required_phys_fields = ["category", "make", "model", "year", "identification_number", "origin_country"]
            for f in required_phys_fields:
                if extra_info.get(f) in [None, ""]:
                    return {"success": False, "error": f"Missing required physical asset field: {f}"}
            self.physical_assets[asset_id] = {
                "asset_id": asset_id,
                "category": extra_info["category"],
                "make": extra_info["make"],
                "model": extra_info["model"],
                "year": extra_info["year"],
                "identification_number": extra_info["identification_number"],
                "origin_country": extra_info["origin_country"],
            }

        return {"success": True, "message": f"Asset '{asset_id}' registered successfully."}

    def update_asset_status(self, asset_id: str, new_status: str) -> dict:
        """
        Change or update the status of an asset (e.g., to "active", "decommissioned").

        Args:
            asset_id (str): The unique identifier for the asset to update.
            new_status (str): The new status value.

        Returns:
            dict:
                On success: { "success": True, "message": "Asset status updated." }
                On failure: { "success": False, "error": <reason> }

        Constraints:
            - The asset with asset_id must exist.
            - The new_status should be non-empty (arbitrary strings allowed if not restricted).
            - Status of an asset must be kept up to date.
        """
        if not isinstance(asset_id, str) or not asset_id:
            return { "success": False, "error": "Invalid asset_id parameter." }
        if not isinstance(new_status, str) or not new_status.strip():
            return { "success": False, "error": "Invalid new_status parameter (empty or not string)." }
        if asset_id not in self.assets:
            return { "success": False, "error": f"Asset with asset_id '{asset_id}' does not exist." }
        self.assets[asset_id]["status"] = new_status.strip()
        return { "success": True, "message": "Asset status updated." }

    def assign_asset_owner(self, asset_id: str, owner_id: str) -> dict:
        """
        Assign a user or department as the new owner of an asset.

        Args:
            asset_id (str): The ID of the asset to update.
            owner_id (str): The ID of the user or department to set as the asset's owner.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Owner of asset <asset_id> assigned to <owner_id>."
                    }
                On failure:
                    {
                        "success": False,
                        "error": "<reason for failure>"
                    }

        Constraints:
            - Asset must exist (identified by asset_id).
            - Owner must exist (identified by owner_id).
            - Ownership must be assignable to a user or department.
        """
        if asset_id not in self.assets:
            return {"success": False, "error": f"Asset with asset_id '{asset_id}' does not exist."}
        if owner_id not in self.owners:
            return {"success": False, "error": f"Owner with owner_id '{owner_id}' does not exist."}
        self.assets[asset_id]['owner_id'] = owner_id
        return {
            "success": True,
            "message": f"Owner of asset {asset_id} assigned to {owner_id}."
        }

    def update_asset_documentation_link(self, asset_id: str, documentation_link: str) -> dict:
        """
        Change or set the documentation link for an asset.

        Args:
            asset_id (str): The unique identifier for the target asset.
            documentation_link (str): The new documentation link to assign.

        Returns:
            dict: 
                - {"success": True, "message": "Documentation link updated for asset <asset_id>"}
                - {"success": False, "error": "<reason>"}

        Constraints:
            - The asset must exist in the system.
            - The documentation link must not be empty (cannot be None or an empty string).
        """
        if asset_id not in self.assets:
            return { "success": False, "error": "Asset not found" }
        if not documentation_link or not isinstance(documentation_link, str) or documentation_link.strip() == "":
            return { "success": False, "error": "Documentation link must not be empty" }
    
        self.assets[asset_id]["documentation_link"] = documentation_link
        return { "success": True, "message": f"Documentation link updated for asset {asset_id}" }

    def add_digital_asset_version(self, asset_id: str, version: str, label: str, url: str) -> dict:
        """
        Add a new version (with version, label, and URL) to the specified digital asset.

        Args:
            asset_id (str): The asset ID of the digital asset.
            version (str): The version string to add.
            label (str): A human-friendly label for this version.
            url (str): The URL where this version can be accessed.

        Returns:
            dict: {
                "success": True,
                "message": str,  # On success, message that version was added.
            }
            or
            {
                "success": False,
                "error": str,    # Reason for failure (asset not found, missing field, duplicate, etc.)
            }

        Constraints:
            - The specified digital asset must exist.
            - All fields (version, label, url) are required and non-empty.
            - Do not add if a version with the same version string already exists for this asset.
        """
        # Check required fields
        if not all([asset_id, version, label, url]):
            return { "success": False, "error": "All fields (asset_id, version, label, url) are required and must be non-empty." }

        # Check if digital asset exists
        if asset_id not in self.digital_assets:
            return { "success": False, "error": f"Digital asset with asset_id '{asset_id}' does not exist." }

        asset = self.digital_assets[asset_id]
        # Check for duplicate version
        for ver_info in asset["available_versions"]:
            if ver_info["version"] == version:
                return { "success": False, "error": f"Version '{version}' already exists for this asset." }

        # Add the new version
        new_version = {
            "version": version,
            "label": label,
            "url": url
        }
        asset["available_versions"].append(new_version)

        return { "success": True, "message": "Version added to digital asset." }

    def update_vehicle_license_plate(self, asset_id: str, new_license_plate: str) -> dict:
        """
        Update the license plate for a vehicle, ensuring uniqueness.

        Args:
            asset_id (str): The unique identifier of the vehicle asset to update.
            new_license_plate (str): The new license plate string.

        Returns:
            dict:
                - On success: { "success": True, "message": "License plate updated successfully." }
                - On failure: { "success": False, "error": <error reason> }

        Constraints:
            - asset_id must correspond to an existing vehicle asset.
            - new_license_plate must not be in use by any other vehicle.
            - If new_license_plate is already assigned to this vehicle, treat as success.
        """
        # 1. Ensure the asset_id exists and refers to a vehicle
        vehicle = self.vehicles.get(asset_id)
        if not vehicle:
            return { "success": False, "error": "Vehicle with the given asset_id does not exist." }

        # 2. Check license plate uniqueness (among all vehicles, other than this one)
        for vid, vinfo in self.vehicles.items():
            if vid != asset_id and vinfo.get("license_plate") == new_license_plate:
                return { "success": False, "error": "The new license plate is already assigned to another vehicle." }

        # 3. If it's the same as the current, treat as success
        if vehicle.get("license_plate") == new_license_plate:
            return { "success": True, "message": "License plate is already assigned to this vehicle." }

        # 4. Update the license plate
        self.vehicles[asset_id]["license_plate"] = new_license_plate
        return { "success": True, "message": "License plate updated successfully." }

    def remove_asset(self, asset_id: str) -> dict:
        """
        Remove/decommission an asset completely from the enterprise asset management system.

        Args:
            asset_id (str): The unique identifier of the asset to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Asset <asset_id> removed from the system."
            }
            or
            {
                "success": False,
                "error": "Asset does not exist."
            }

        Constraints:
            - asset_id must exist in the system.
            - Associated entries in specialized tables (digital_assets, physical_assets, vehicles) must also be removed if present.
        """
        # Check if asset exists
        if asset_id not in self.assets:
            return {"success": False, "error": "Asset does not exist."}

        # Remove from main assets table
        del self.assets[asset_id]

        # Remove from digital assets if present
        if asset_id in self.digital_assets:
            del self.digital_assets[asset_id]

        # Remove from physical assets if present
        if asset_id in self.physical_assets:
            del self.physical_assets[asset_id]

        # Remove from vehicles if present
        if asset_id in self.vehicles:
            del self.vehicles[asset_id]

        return {"success": True, "message": f"Asset {asset_id} removed from the system."}

    def update_physical_asset_info(
        self,
        asset_id: str,
        category: str = None,
        make: str = None,
        model: str = None,
        year: int = None,
        identification_number: str = None,
        origin_country: str = None
    ) -> dict:
        """
        Edit physical asset details. Only provided (non-None) fields will be updated.

        Args:
            asset_id (str): The unique ID of the physical asset to update.
            category (str, optional): The asset's category (e.g., 'equipment', 'vehicle').
            make (str, optional): Manufacturer of the asset.
            model (str, optional): Model of the asset.
            year (int, optional): Year of manufacture.
            identification_number (str, optional): Serial or other unique identifier.
            origin_country (str, optional): Country of origin.

        Returns:
            dict: {
                "success": True,
                "message": "Physical asset info updated."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - asset_id must exist in the physical assets.
            - Only provided fields will be updated (at least one must be provided).
            - If any updated value is of incorrect type, operation fails.
        """
        if asset_id not in self.physical_assets:
            return { "success": False, "error": "Physical asset does not exist." }

        asset = self.physical_assets[asset_id]
        updated = False
        # Check and update each possible field if provided (None is "not provided")
        if category is not None:
            if not isinstance(category, str):
                return { "success": False, "error": "Invalid type for category." }
            asset["category"] = category
            updated = True
        if make is not None:
            if not isinstance(make, str):
                return { "success": False, "error": "Invalid type for make." }
            asset["make"] = make
            updated = True
        if model is not None:
            if not isinstance(model, str):
                return { "success": False, "error": "Invalid type for model." }
            asset["model"] = model
            updated = True
        if year is not None:
            if not isinstance(year, int):
                return { "success": False, "error": "Invalid type for year, must be int." }
            asset["year"] = year
            updated = True
        if identification_number is not None:
            if not isinstance(identification_number, str):
                return { "success": False, "error": "Invalid type for identification_number." }
            asset["identification_number"] = identification_number
            updated = True
        if origin_country is not None:
            if not isinstance(origin_country, str):
                return { "success": False, "error": "Invalid type for origin_country." }
            asset["origin_country"] = origin_country
            updated = True

        if not updated:
            return { "success": False, "error": "No valid fields provided to update." }

        # Save back (for in-place dict this is redundant, but for clarity)
        self.physical_assets[asset_id] = asset

        return { "success": True, "message": "Physical asset info updated." }

    def update_owner_info(
        self,
        owner_id: str,
        name: str = None,
        contact_info: str = None,
        owner_type: str = None
    ) -> dict:
        """
        Edit owner information for a user or department.

        Args:
            owner_id (str): The unique identifier for the owner to update.
            name (str, optional): The new name for the owner.
            contact_info (str, optional): The new contact information.
            owner_type (str, optional): The new type for the owner (e.g., 'user', 'department').

        Returns:
            dict: 
                - On success: 
                    {"success": True, "message": "Owner information updated successfully."}
                - On failure: 
                    {"success": False, "error": "Owner ID does not exist."}

        Constraints:
            - The provided owner_id must exist in the system.
            - Only provided fields will be updated.
        """
        if owner_id not in self.owners:
            return {"success": False, "error": "Owner ID does not exist."}

        owner_info = self.owners[owner_id]
        if name is not None:
            owner_info['name'] = name
        if contact_info is not None:
            owner_info['contact_info'] = contact_info
        if owner_type is not None:
            owner_info['owner_type'] = owner_type

        # Assign the updated owner info back (not strictly necessary for dict, but for clarity)
        self.owners[owner_id] = owner_info

        return {"success": True, "message": "Owner information updated successfully."}

    def validate_asset_uniqueness(self, asset_id: str) -> dict:
        """
        Check whether the provided asset_id is unique in the asset registry.

        Args:
            asset_id (str): The proposed unique identifier for a new asset.

        Returns:
            dict: {
                "success": True,
                "message": "Asset ID is unique and can be used."
            } if asset_id does not exist,
            or
            {
                "success": False,
                "error": "Asset ID already exists."
            } if asset_id is already present in the registry.

        Constraints:
            - Each asset must have a unique asset_id across all asset types and subtypes.
        """
        if (
            asset_id in self.assets
            or asset_id in self.digital_assets
            or asset_id in self.physical_assets
            or asset_id in self.vehicles
        ):
            return {
                "success": False,
                "error": "Asset ID already exists."
            }
        return {
            "success": True,
            "message": "Asset ID is unique and can be used."
        }


class EnterpriseAssetManagementSystem(BaseEnv):
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

    def get_digital_asset_by_software_name(self, **kwargs):
        return self._call_inner_tool('get_digital_asset_by_software_name', kwargs)

    def list_digital_asset_versions(self, **kwargs):
        return self._call_inner_tool('list_digital_asset_versions', kwargs)

    def get_asset_by_id(self, **kwargs):
        return self._call_inner_tool('get_asset_by_id', kwargs)

    def get_vehicle_by_license_plate(self, **kwargs):
        return self._call_inner_tool('get_vehicle_by_license_plate', kwargs)

    def get_physical_asset_by_id(self, **kwargs):
        return self._call_inner_tool('get_physical_asset_by_id', kwargs)

    def list_assets_by_owner(self, **kwargs):
        return self._call_inner_tool('list_assets_by_owner', kwargs)

    def get_owner_info(self, **kwargs):
        return self._call_inner_tool('get_owner_info', kwargs)

    def list_assets_by_type(self, **kwargs):
        return self._call_inner_tool('list_assets_by_type', kwargs)

    def check_asset_status(self, **kwargs):
        return self._call_inner_tool('check_asset_status', kwargs)

    def get_asset_documentation_link(self, **kwargs):
        return self._call_inner_tool('get_asset_documentation_link', kwargs)

    def validate_digital_asset_versions_structure(self, **kwargs):
        return self._call_inner_tool('validate_digital_asset_versions_structure', kwargs)

    def add_new_asset(self, **kwargs):
        return self._call_inner_tool('add_new_asset', kwargs)

    def update_asset_status(self, **kwargs):
        return self._call_inner_tool('update_asset_status', kwargs)

    def assign_asset_owner(self, **kwargs):
        return self._call_inner_tool('assign_asset_owner', kwargs)

    def update_asset_documentation_link(self, **kwargs):
        return self._call_inner_tool('update_asset_documentation_link', kwargs)

    def add_digital_asset_version(self, **kwargs):
        return self._call_inner_tool('add_digital_asset_version', kwargs)

    def update_vehicle_license_plate(self, **kwargs):
        return self._call_inner_tool('update_vehicle_license_plate', kwargs)

    def remove_asset(self, **kwargs):
        return self._call_inner_tool('remove_asset', kwargs)

    def update_physical_asset_info(self, **kwargs):
        return self._call_inner_tool('update_physical_asset_info', kwargs)

    def update_owner_info(self, **kwargs):
        return self._call_inner_tool('update_owner_info', kwargs)

    def validate_asset_uniqueness(self, **kwargs):
        return self._call_inner_tool('validate_asset_uniqueness', kwargs)
