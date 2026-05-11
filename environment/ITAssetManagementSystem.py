# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict



class AssetInfo(TypedDict):
    asset_id: str
    asset_type: str
    asset_name: str
    owner_id: str
    location: str
    purchase_date: str
    status: str
    configuration: str
    security_level: str
    compliance_status: str
    lifecycle_sta: str

class OwnerInfo(TypedDict):
    owner_id: str
    owner_name: str
    department: str
    contact_info: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Assets: {asset_id: AssetInfo}
        self.assets: Dict[str, AssetInfo] = {}
        # Owners: {owner_id: OwnerInfo}
        self.owners: Dict[str, OwnerInfo] = {}
        # Constraints:
        # - Each asset must have a unique asset_id.
        # - Asset types are restricted to predefined categories (hardware, software, network device, etc.).
        # - Security level values must conform to organization-defined schemes (e.g., "High", "Medium", "Low" or numerical tiers).
        # - Each asset must be trackable through its full lifecycle (e.g., acquisition, deployment, retirement).
        # - Asset status, compliance, and security status must be up to date for accurate reporting.

    def get_asset_by_id(self, asset_id: str) -> dict:
        """
        Retrieve the full details (metadata) of an asset by its unique asset_id.

        Args:
            asset_id (str): The unique identifier for the asset.

        Returns:
            dict: {
                "success": True,
                "data": AssetInfo  # Asset information dictionary
            }
            or
            {
                "success": False,
                "error": str  # e.g., "Asset not found"
            }

        Constraints:
            - Each asset must have a unique asset_id.
            - If asset_id does not exist, return error.
        """
        asset = self.assets.get(asset_id)
        if asset is None:
            return { "success": False, "error": "Asset not found" }
        return { "success": True, "data": asset }

    def get_asset_by_name(self, asset_name: str) -> dict:
        """
        Retrieve asset details by `asset_name`.

        Args:
            asset_name (str): The name of the asset to retrieve (exact match).

        Returns:
            dict: {
                "success": True,
                "data": List[AssetInfo]  # List of matching asset info dicts (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Description of error (e.g. invalid input)
            }
        """
        if not isinstance(asset_name, str) or not asset_name.strip():
            return { "success": False, "error": "Invalid or empty asset_name provided." }

        # Exact match (case sensitive)
        result = [
            asset for asset in self.assets.values()
            if asset["asset_name"] == asset_name
        ]

        return { "success": True, "data": result }

    def list_assets_by_type(self, asset_type: str) -> dict:
        """
        List all assets filtered by asset_type.

        Args:
            asset_type (str): The asset type to filter by (e.g., "hardware", "software", "network device").

        Returns:
            dict: {
                "success": True,
                "data": List[AssetInfo]  # All assets whose asset_type matches (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Description of why the listing failed (e.g., invalid type)
            }

        Constraints:
            - asset_type must be one of the predefined categories.
        """

        # Define allowed asset types (should ideally be a class variable or config)
        allowed_types = {"hardware", "software", "network device"}  

        if asset_type not in allowed_types:
            return {"success": False, "error": "Invalid asset type"}

        filtered_assets = [
            asset for asset in self.assets.values()
            if asset["asset_type"] == asset_type
        ]

        return {"success": True, "data": filtered_assets}

    def list_assets_by_owner(self, owner_id: str = None, owner_name: str = None) -> dict:
        """
        Return all assets assigned to a given owner, queried by owner_id or owner_name.

        Args:
            owner_id (str, optional): The owner's unique identifier.
            owner_name (str, optional): The owner's name.

        Returns:
            dict: {
                "success": True,
                "data": List[AssetInfo]  # List of matching assets (can be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (owner not found, both parameters missing, etc.)
            }

        Constraints:
            - At least one of owner_id or owner_name must be provided.
            - If both provided, owner_id is used.
            - The owner must exist.
        """
        # Must specify at least one identifier
        if not owner_id and not owner_name:
            return { "success": False, "error": "Either owner_id or owner_name must be provided" }

        actual_owner_id = None

        if owner_id:
            if owner_id not in self.owners:
                return { "success": False, "error": "Owner with provided owner_id does not exist" }
            actual_owner_id = owner_id
        else:
            # Search for owner_name
            matches = [oid for oid, info in self.owners.items() if info["owner_name"] == owner_name]
            if not matches:
                return { "success": False, "error": "Owner with provided owner_name does not exist" }
            if len(matches) > 1:
                # Ambiguous owner_name
                return { "success": False, "error": "Multiple owners found with given owner_name; provide owner_id" }
            actual_owner_id = matches[0]

        # Now, actual_owner_id is valid
        owned_assets = [
            asset_info for asset_info in self.assets.values()
            if asset_info["owner_id"] == actual_owner_id
        ]

        return { "success": True, "data": owned_assets }

    def get_asset_status(self, asset_id: str) -> dict:
        """
        Retrieve the current status of a specified asset.

        Args:
            asset_id (str): The unique identifier of the asset.

        Returns:
            dict: 
                - If found: { "success": True, "data": <status_str> }  
                - If not found: { "success": False, "error": "Asset not found" }

        Constraints:
            - asset_id must exist in the system.
            - Returns status attribute such as "in use", "in storage", "retired", etc.
        """
        asset = self.assets.get(asset_id)
        if not asset:
            return { "success": False, "error": "Asset not found" }
        return { "success": True, "data": asset["status"] }

    def get_asset_security_level(self, asset_id: str) -> dict:
        """
        Obtain the security level classification of an asset by its asset_id.

        Args:
            asset_id (str): Unique identifier of the asset.

        Returns:
            dict:
                - success=True, data=str: security level of the asset.
                - success=False, error=str: error message if asset does not exist.

        Constraints:
            - asset_id must exist in the system.
        """
        asset = self.assets.get(asset_id)
        if asset is None:
            return {"success": False, "error": "Asset not found"}
        return {"success": True, "data": asset["security_level"]}

    def get_asset_compliance_status(self, asset_id: str) -> dict:
        """
        Query the compliance status of an asset.

        Args:
            asset_id (str): The unique ID of the asset you want to look up.

        Returns:
            dict: {
                "success": True,
                "data": str  # The compliance_status of the asset
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g., asset not found
            }

        Constraints:
            - Asset must exist in the system (asset_id in self.assets).
        """
        asset = self.assets.get(asset_id)
        if asset is None:
            return {"success": False, "error": "Asset not found"}
        return {"success": True, "data": asset.get("compliance_status", "")}

    def get_asset_lifecycle_stage(self, asset_id: str) -> dict:
        """
        Retrieve the current lifecycle stage (e.g., acquisition, deployment, retirement) of the specified asset.

        Args:
            asset_id (str): The unique identifier of the asset.

        Returns:
            dict: 
                On success: {
                    "success": True,
                    "data": {
                        "asset_id": str,
                        "lifecycle_stage": str
                    }
                }
                On failure: {
                    "success": False,
                    "error": "Asset not found"
                }

        Constraints:
            - The provided asset_id must correspond to an existing asset.
        """
        asset = self.assets.get(asset_id)
        if not asset:
            return { "success": False, "error": "Asset not found" }
    
        return {
            "success": True,
            "data": {
                "asset_id": asset_id,
                "lifecycle_stage": asset["lifecycle_sta"]
            }
        }

    def get_assets_by_location(self, location: str) -> dict:
        """
        List all assets present at a specified physical or network location.

        Args:
            location (str): The physical or network location to query assets by.

        Returns:
            dict: {
                "success": True,
                "data": List[AssetInfo]  # List of asset information dicts matching the location.
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g., invalid location specified.
            }

        Constraints:
            - location string must be non-empty.
        """
        if not location or not isinstance(location, str) or location.strip() == "":
            return { "success": False, "error": "Invalid location specified" }

        matching_assets = [
            asset_info for asset_info in self.assets.values()
            if asset_info["location"] == location
        ]
        return { "success": True, "data": matching_assets }

    def get_owner_by_id(self, owner_id: str) -> dict:
        """
        Fetch owner details using owner_id.

        Args:
            owner_id (str): The unique identifier for the owner to look up.

        Returns:
            dict: {
                "success": True,
                "data": OwnerInfo  # Owner information as a dictionary
            }
            or
            {
                "success": False,
                "error": str  # Description if owner is not found
            }

        Constraints:
            - owner_id must exist in the system.
        """
        if owner_id in self.owners:
            return { "success": True, "data": self.owners[owner_id] }
        else:
            return { "success": False, "error": "Owner not found" }

    def get_owner_by_name(self, owner_name: str) -> dict:
        """
        Fetch owner details using owner_name (case-insensitive search).

        Args:
            owner_name (str): The name of the owner to search.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "data": List[OwnerInfo]  # List of owner records with matching name (may be length 1 or more)
                }
                On error:
                {
                    "success": False,
                    "error": "Owner not found"
                }
        Notes:
            - If multiple owners share the same name, all are returned in the data list.
            - Matching is case-insensitive.
        """
        matches = [
            owner_info for owner_info in self.owners.values()
            if owner_info['owner_name'].lower() == owner_name.lower()
        ]

        if not matches:
            return { "success": False, "error": "Owner not found" }

        return { "success": True, "data": matches }

    def list_all_assets(self) -> dict:
        """
        Retrieve a complete list of all tracked assets in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[AssetInfo]  # List of all asset info (can be empty if no assets tracked)
            }
        """
        all_assets = list(self.assets.values())
        return { "success": True, "data": all_assets }

    def list_all_owners(self) -> dict:
        """
        Retrieve the list of all asset owners in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[OwnerInfo]  # List of all asset owner records (can be empty)
            }

        Constraints:
            - No input parameters.
            - No specific constraints apply for this operation.
        """
        owners_list = list(self.owners.values())
        return {
            "success": True,
            "data": owners_list
        }

    def list_assets_by_security_level(self, security_level: str) -> dict:
        """
        List all assets with the specified security level.

        Args:
            security_level (str): The security level to filter assets by (e.g., "High", "Medium", "Low").

        Returns:
            dict: {
                "success": True,
                "data": List[AssetInfo]  # May be an empty list if no assets match
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., invalid security level)
            }

        Constraints:
            - security_level must conform to organization-defined schemes
            - The function does not error if there are zero matches (success with empty list)
        """
        # Example allowed security levels; update as needed for the actual scheme
        allowed_security_levels = {"High", "Medium", "Low"}
        if security_level not in allowed_security_levels:
            return {
                "success": False,
                "error": f"Invalid security_level: '{security_level}'. Allowed are {sorted(allowed_security_levels)}"
            }

        result = [
            asset for asset in self.assets.values()
            if asset["security_level"] == security_level
        ]
        return {"success": True, "data": result}

    def update_asset_status(self, asset_id: str, new_status: str) -> dict:
        """
        Modifies the status field of a specified asset.

        Args:
            asset_id (str): The unique identifier of the asset whose status should be updated.
            new_status (str): The new status value to assign to the asset.

        Returns:
            dict:
                On success:
                    {"success": True, "message": "Asset status updated successfully."}
                On failure:
                    {"success": False, "error": "<reason>"}

        Constraints:
            - The asset must exist in the system.
            - The status will be updated regardless of previous value.
        """
        asset = self.assets.get(asset_id)
        if asset is None:
            return {"success": False, "error": "Asset with the given asset_id does not exist."}
    
        asset['status'] = new_status
        return {"success": True, "message": "Asset status updated successfully."}

    def update_asset_security_level(self, asset_id: str, new_security_level: str) -> dict:
        """
        Update the security_level of an asset to a different organization-approved value.

        Args:
            asset_id (str): The unique identifier of the asset.
            new_security_level (str): The new security level to set (must be organization-approved).

        Returns:
            dict: {
                "success": True,
                "message": "Asset security level updated"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - asset_id must exist.
            - new_security_level must be in approved organization-level security_levels.
        """
        # For constraint enforcement, presume security_levels is an attribute set or list on the class.
        approved_levels = getattr(self, 'security_levels', {'High', 'Medium', 'Low'})
    
        if asset_id not in self.assets:
            return { "success": False, "error": "Asset not found" }
    
        if new_security_level not in approved_levels:
            return { "success": False, "error": f"Security level '{new_security_level}' is not organization-approved" }

        self.assets[asset_id]['security_level'] = new_security_level
    
        # If real environment would need to update status/compliance/etc., not required by this operation spec.
        return { "success": True, "message": "Asset security level updated" }

    def update_asset_compliance_status(self, asset_id: str, new_compliance_status: str) -> dict:
        """
        Change the compliance_status of a specific asset.

        Args:
            asset_id (str): The unique identifier of the asset.
            new_compliance_status (str): The new compliance status to set for the asset.

        Returns:
            dict: {
                "success": True,
                "message": "Asset compliance status updated successfully."
            }
            OR
            {
                "success": False,
                "error": "Asset does not exist"
            }

        Constraints:
            - asset_id must exist in the system.
            - No restrictions are enforced here on the values for compliance_status.
        """
        asset = self.assets.get(asset_id)
        if asset is None:
            return {"success": False, "error": "Asset does not exist"}

        asset["compliance_status"] = new_compliance_status
        return {"success": True, "message": "Asset compliance status updated successfully."}

    def update_asset_lifecycle_stage(self, asset_id: str, new_lifecycle_stage: str) -> dict:
        """
        Update the lifecycle stage of a specified asset.

        Args:
            asset_id (str): Unique identifier for the asset to update.
            new_lifecycle_stage (str): The new lifecycle stage value (e.g., "acquisition", "deployment", "retirement").

        Returns:
            dict: {
                "success": True,
                "message": "Asset lifecycle stage updated."
            }
            or
            {
                "success": False,
                "error": "Asset not found."
            }

        Constraints:
            - Asset with asset_id must exist.
            - (Optionally) new_lifecycle_stage should be a valid lifecycle value (not enforced here as not specified).
        """
        asset = self.assets.get(asset_id)
        if not asset:
            return { "success": False, "error": "Asset not found." }

        asset["lifecycle_sta"] = new_lifecycle_stage
        return { "success": True, "message": f"Asset {asset_id} lifecycle stage updated to '{new_lifecycle_stage}'." }

    def reassign_asset_owner(self, asset_id: str, new_owner_id: str) -> dict:
        """
        Change the owner of a specific asset to another owner.

        Args:
            asset_id (str): The asset's unique identifier.
            new_owner_id (str): The owner_id of the new owner.

        Returns:
            dict:
                - On success:
                    {"success": True, "message": "Asset owner reassigned to <new_owner_id>"}
                - If asset not found:
                    {"success": False, "error": "Asset not found"}
                - If new owner not found:
                    {"success": False, "error": "New owner not found"}
                - If asset already assigned to new_owner_id:
                    {"success": True, "message": "Asset already assigned to this owner"}

        Constraints:
            - asset_id must already exist.
            - new_owner_id must already exist.
        """
        asset = self.assets.get(asset_id)
        if not asset:
            return {"success": False, "error": "Asset not found"}

        if new_owner_id not in self.owners:
            return {"success": False, "error": "New owner not found"}

        if asset["owner_id"] == new_owner_id:
            return {"success": True, "message": "Asset already assigned to this owner"}

        asset["owner_id"] = new_owner_id
        return {"success": True, "message": f"Asset owner reassigned to {new_owner_id}"}

    def update_asset_configuration(self, asset_id: str, new_configuration: str) -> dict:
        """
        Record changes to the configuration attribute of a specified asset.

        Args:
            asset_id (str): The unique identifier for the asset.
            new_configuration (str): The new configuration value for the asset.

        Returns:
            dict: {
                "success": True,
                "message": "Configuration updated for asset <asset_id>"
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., asset not found)
            }
    
        Constraints:
            - Asset with asset_id must exist in the system.
            - No specific validation on the new_configuration content.
        """
        if asset_id not in self.assets:
            return { "success": False, "error": "Asset not found" }
        self.assets[asset_id]["configuration"] = new_configuration
        return { "success": True, "message": f"Configuration updated for asset {asset_id}" }

    def update_asset_location(self, asset_id: str, new_location: str) -> dict:
        """
        Change the location attribute of an asset.

        Args:
            asset_id (str): Unique identifier of the asset to update.
            new_location (str): The new location string for the asset.

        Returns:
            dict:
                - On success: { "success": True, "message": "Asset location updated successfully." }
                - On failure (asset not found): { "success": False, "error": "Asset not found." }

        Constraints:
            - Asset must exist in the system.
            - No restriction on content/format of new_location from environment spec.
        """
        if asset_id not in self.assets:
            return {"success": False, "error": "Asset not found."}
    
        self.assets[asset_id]["location"] = new_location
        return {"success": True, "message": "Asset location updated successfully."}

    def add_new_asset(
        self,
        asset_id: str,
        asset_type: str,
        asset_name: str,
        owner_id: str,
        location: str,
        purchase_date: str,
        status: str,
        configuration: str,
        security_level: str,
        compliance_status: str,
        lifecycle_sta: str
    ) -> dict:
        """
        Insert a new asset record, ensuring:
          - asset_id is unique
          - asset_type is in allowed set
          - security_level is in allowed set
          - owner_id exists
          - All required fields are present

        Args:
            asset_id (str): Unique identifier for the asset.
            asset_type (str): One of allowed types ("hardware", "software", "network device").
            asset_name (str): Name of the asset.
            owner_id (str): Existing owner ID.
            location (str): Asset location.
            purchase_date (str): Purchase date string.
            status (str): Asset status.
            configuration (str): Asset configuration description.
            security_level (str): One of ("High", "Medium", "Low").
            compliance_status (str): Asset compliance status.
            lifecycle_sta (str): Asset lifecycle stage string.

        Returns:
            dict: {
              "success": True, "message": "Asset <asset_id> added successfully."
            }
            or
            dict: {
              "success": False, "error": <reason>
            }
        """
        allowed_types = {"hardware", "software", "network device"}
        allowed_security_levels = {"High", "Medium", "Low"}

        # Check uniqueness of asset_id
        if asset_id in self.assets:
            return { "success": False, "error": f"Asset ID '{asset_id}' already exists." }

        # Check asset_type
        if asset_type not in allowed_types:
            return { "success": False, "error": f"Invalid asset_type '{asset_type}'. Must be one of {sorted(allowed_types)}." }

        # Check security_level
        if security_level not in allowed_security_levels:
            return { "success": False, "error": f"Invalid security_level '{security_level}'. Must be one of {sorted(allowed_security_levels)}." }

        # Check owner_id exists
        if owner_id not in self.owners:
            return { "success": False, "error": f"Owner ID '{owner_id}' does not exist." }

        # Compose the AssetInfo dictionary
        asset_info = {
            "asset_id": asset_id,
            "asset_type": asset_type,
            "asset_name": asset_name,
            "owner_id": owner_id,
            "location": location,
            "purchase_date": purchase_date,
            "status": status,
            "configuration": configuration,
            "security_level": security_level,
            "compliance_status": compliance_status,
            "lifecycle_sta": lifecycle_sta
        }

        self.assets[asset_id] = asset_info

        return { "success": True, "message": f"Asset {asset_id} added successfully." }

    def delete_asset(self, asset_id: str) -> dict:
        """
        Remove an asset from the management system.

        Args:
            asset_id (str): The unique identifier of the asset to remove.

        Returns:
            dict:
                On success:
                    {
                      "success": True,
                      "message": "Asset <asset_id> deleted successfully."
                    }
                On failure:
                    {
                      "success": False,
                      "error": "Asset not found."
                    }

        Constraints:
            - Asset must exist in the management system.
            - Asset is completely removed from the tracking database.
        """
        if asset_id not in self.assets:
            return { "success": False, "error": "Asset not found." }
        del self.assets[asset_id]
        return { "success": True, "message": f"Asset {asset_id} deleted successfully." }

    def add_new_owner(self, owner_id: str, owner_name: str, department: str, contact_info: str) -> dict:
        """
        Add a new owner (person or department) to the system.

        Args:
            owner_id (str): Unique identifier for the owner.
            owner_name (str): Name of the owner.
            department (str): Department associated with the owner.
            contact_info (str): Contact details (e.g., email, phone).

        Returns:
            dict: {
                "success": True,
                "message": "Owner <owner_id> added successfully."
            }
            or
            {
                "success": False,
                "error": "Reason for failure."
            }
    
        Constraints:
            - owner_id must be unique.
            - All fields are required and must be non-empty.
        """
        # Basic input validation
        if not all([owner_id, owner_name, department, contact_info]):
            return {"success": False, "error": "All fields (owner_id, owner_name, department, contact_info) are required and must be non-empty."}
    
        if owner_id in self.owners:
            return {"success": False, "error": "Owner ID already exists."}

        owner_info: OwnerInfo = {
            "owner_id": owner_id,
            "owner_name": owner_name,
            "department": department,
            "contact_info": contact_info
        }
        self.owners[owner_id] = owner_info
        return {"success": True, "message": f"Owner {owner_id} added successfully."}

    def update_owner_details(
        self,
        owner_id: str,
        owner_name: str = None,
        department: str = None,
        contact_info: str = None
    ) -> dict:
        """
        Modify owner metadata (name, department, contact_info).

        Args:
            owner_id (str): Owner's unique identifier to be updated.
            owner_name (str, optional): New name for the owner.
            department (str, optional): New department.
            contact_info (str, optional): New contact info.

        Returns:
            dict: {
                "success": True,
                "message": "Owner details updated for owner_id <owner_id>"
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Only owner_name, department, and contact_info may be updated.
            - owner_id must already exist in the system.
        """
        if owner_id not in self.owners:
            return { "success": False, "error": "Owner ID not found" }

        owner = self.owners[owner_id]
        updated = False

        if owner_name is not None:
            owner["owner_name"] = owner_name
            updated = True
        if department is not None:
            owner["department"] = department
            updated = True
        if contact_info is not None:
            owner["contact_info"] = contact_info
            updated = True

        if updated:
            return {
                "success": True,
                "message": f"Owner details updated for owner_id {owner_id}"
            }
        else:
            return {
                "success": True,
                "message": f"No changes provided. Owner info for owner_id {owner_id} remains unchanged."
            }


class ITAssetManagementSystem(BaseEnv):
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

    def get_asset_by_id(self, **kwargs):
        return self._call_inner_tool('get_asset_by_id', kwargs)

    def get_asset_by_name(self, **kwargs):
        return self._call_inner_tool('get_asset_by_name', kwargs)

    def list_assets_by_type(self, **kwargs):
        return self._call_inner_tool('list_assets_by_type', kwargs)

    def list_assets_by_owner(self, **kwargs):
        return self._call_inner_tool('list_assets_by_owner', kwargs)

    def get_asset_status(self, **kwargs):
        return self._call_inner_tool('get_asset_status', kwargs)

    def get_asset_security_level(self, **kwargs):
        return self._call_inner_tool('get_asset_security_level', kwargs)

    def get_asset_compliance_status(self, **kwargs):
        return self._call_inner_tool('get_asset_compliance_status', kwargs)

    def get_asset_lifecycle_stage(self, **kwargs):
        return self._call_inner_tool('get_asset_lifecycle_stage', kwargs)

    def get_assets_by_location(self, **kwargs):
        return self._call_inner_tool('get_assets_by_location', kwargs)

    def get_owner_by_id(self, **kwargs):
        return self._call_inner_tool('get_owner_by_id', kwargs)

    def get_owner_by_name(self, **kwargs):
        return self._call_inner_tool('get_owner_by_name', kwargs)

    def list_all_assets(self, **kwargs):
        return self._call_inner_tool('list_all_assets', kwargs)

    def list_all_owners(self, **kwargs):
        return self._call_inner_tool('list_all_owners', kwargs)

    def list_assets_by_security_level(self, **kwargs):
        return self._call_inner_tool('list_assets_by_security_level', kwargs)

    def update_asset_status(self, **kwargs):
        return self._call_inner_tool('update_asset_status', kwargs)

    def update_asset_security_level(self, **kwargs):
        return self._call_inner_tool('update_asset_security_level', kwargs)

    def update_asset_compliance_status(self, **kwargs):
        return self._call_inner_tool('update_asset_compliance_status', kwargs)

    def update_asset_lifecycle_stage(self, **kwargs):
        return self._call_inner_tool('update_asset_lifecycle_stage', kwargs)

    def reassign_asset_owner(self, **kwargs):
        return self._call_inner_tool('reassign_asset_owner', kwargs)

    def update_asset_configuration(self, **kwargs):
        return self._call_inner_tool('update_asset_configuration', kwargs)

    def update_asset_location(self, **kwargs):
        return self._call_inner_tool('update_asset_location', kwargs)

    def add_new_asset(self, **kwargs):
        return self._call_inner_tool('add_new_asset', kwargs)

    def delete_asset(self, **kwargs):
        return self._call_inner_tool('delete_asset', kwargs)

    def add_new_owner(self, **kwargs):
        return self._call_inner_tool('add_new_owner', kwargs)

    def update_owner_details(self, **kwargs):
        return self._call_inner_tool('update_owner_details', kwargs)

