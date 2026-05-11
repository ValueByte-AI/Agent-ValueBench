# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
from datetime import datetime



# -- TypedDicts mirroring the state space entities --

class FundHouseInfo(TypedDict):
    fund_house_id: str
    name: str  # Corrected from typo 'nam'

class SchemeInfo(TypedDict):
    scheme_id: str
    name: str
    fund_house_id: str  # links to FundHouse
    asset_class_id: str  # links to AssetClass
    launch_date: str
    status: str  # Corrected from typo 'sta'

class AssetClassInfo(TypedDict):
    asset_class_id: str
    name: str
    description: str

class NAVRecordInfo(TypedDict):
    nav_record_id: str
    scheme_id: str  # links to Scheme
    nav_value: float
    nav_date: str  # Corrected from typo 'nav_da'

class _GeneratedEnvImpl:
    def __init__(self):
        # FundHouse: {fund_house_id: FundHouseInfo}
        self.fund_houses: Dict[str, FundHouseInfo] = {}
        # Scheme: {scheme_id: SchemeInfo}
        self.schemes: Dict[str, SchemeInfo] = {}
        # AssetClass: {asset_class_id: AssetClassInfo}
        self.asset_classes: Dict[str, AssetClassInfo] = {}
        # NAVRecord: {nav_record_id: NAVRecordInfo}
        self.nav_records: Dict[str, NAVRecordInfo] = {}

        # Constraints:
        # - Each Scheme links to exactly one FundHouse and one AssetClass.
        # - Only the latest NAVRecord per Scheme is reported as the "latest NAV".
        # - NAVRecords must be for valid calendar dates; updates are typically daily.
        # - Only schemes with status 'active' typically appear in user queries.

    def get_fund_house_by_name(self, name: str) -> dict:
        """
        Retrieve fund house information and fund_house_id by specifying the fund house name.

        Args:
            name (str): The name of the fund house.

        Returns:
            dict: {
                "success": True,
                "data": FundHouseInfo  # all info fields, including fund_house_id
            }
            or
            {
                "success": False,
                "error": str  # Description if not found
            }

        Constraints:
            - Fund house name must exist in the system.
        """
        for fh in self.fund_houses.values():
            if fh["name"] == name:
                return { "success": True, "data": fh }
        return { "success": False, "error": "Fund house with given name not found" }

    def list_schemes_by_fund_house(self, fund_house_id: str, status: str = None) -> dict:
        """
        List all schemes belonging to the specified fund house.
        Optionally filter by scheme status ('active', 'inactive', or other status values).

        Args:
            fund_house_id (str): The unique identifier for the fund house.
            status (str, optional): Restrict results to schemes with this status. If None, return all.

        Returns:
            dict: 
                - On success: {"success": True, "data": List[SchemeInfo]}
                - On error:   {"success": False, "error": str}

        Constraints:
            - Fund house must exist.
            - Each scheme is linked to a fund house by fund_house_id.
            - If status is specified, only schemes with that status are returned.
        """
        if fund_house_id not in self.fund_houses:
            return { "success": False, "error": "Fund house does not exist" }

        result = [
            scheme for scheme in self.schemes.values()
            if scheme["fund_house_id"] == fund_house_id and (status is None or scheme.get("status") == status)
        ]
        return { "success": True, "data": result }

    def get_scheme_by_name_and_fund_house(self, name: str, fund_house_id: str) -> dict:
        """
        Retrieve scheme info (SchemeInfo) using the scheme name and the associated fund house ID.

        Args:
            name (str): The name of the mutual fund scheme.
            fund_house_id (str): The ID of the fund house.

        Returns:
            dict:
                Success: { "success": True, "data": SchemeInfo }
                Failure: { "success": False, "error": "Scheme not found for given name and fund house" }
                         or { "success": False, "error": "Fund house does not exist" }

        Constraints:
            - fund_house_id must exist in the environment.
            - The scheme must exist with the specified name and fund_house_id.
            - If multiple schemes match (should not happen), return the first found.
        """
        if fund_house_id not in self.fund_houses:
            return { "success": False, "error": "Fund house does not exist" }

        for scheme in self.schemes.values():
            if scheme["name"] == name and scheme["fund_house_id"] == fund_house_id:
                return { "success": True, "data": scheme }

        return { "success": False, "error": "Scheme not found for given name and fund house" }

    def list_active_schemes_by_fund_house(self, fund_house_id: str) -> dict:
        """
        List all 'active' schemes under the specified fund house.

        Args:
            fund_house_id (str): The unique identifier for the fund house.

        Returns:
            dict: {
                "success": True,
                "data": List[SchemeInfo]  # All active schemes for the given fund house, may be empty
            }
            or
            {
                "success": False,
                "error": str  # Description if fund house does not exist
            }

        Constraints:
            - The fund house must exist in the system.
            - Only schemes where status == 'active' are returned.
        """
        if fund_house_id not in self.fund_houses:
            return { "success": False, "error": "Fund house not found" }

        active_schemes = [
            scheme for scheme in self.schemes.values()
            if scheme["fund_house_id"] == fund_house_id and scheme.get("status") == "active"
        ]

        return { "success": True, "data": active_schemes }

    def get_scheme_status(self, scheme_id: str) -> dict:
        """
        Retrieve the current status ("active", "inactive", etc.) of the scheme identified by scheme_id.

        Args:
            scheme_id (str): The unique identifier of the mutual fund scheme.

        Returns:
            dict:
                On success:
                {
                    "success": True,
                    "data": {
                        "scheme_id": str,
                        "status": str
                    }
                }
                On failure (e.g., scheme not found):
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - scheme_id must exist in the system.
        """
        scheme = self.schemes.get(scheme_id)
        if not scheme:
            return {"success": False, "error": "Scheme not found"}
        return {"success": True, "data": {"scheme_id": scheme_id, "status": scheme["status"]}}

    def get_latest_nav_for_scheme(self, scheme_id: str) -> dict:
        """
        Retrieve the most recent NAVRecord (NAV value and date) for a given scheme.

        Args:
            scheme_id (str): The ID of the mutual fund scheme.

        Returns:
            - If a latest NAVRecord exists for the scheme:
                {"success": True, "data": NAVRecordInfo}
            - If the scheme does not exist:
                {"success": False, "error": "Scheme does not exist"}
            - If there is no NAVRecord for the scheme:
                {"success": False, "error": "No NAV records found for scheme"}
        Constraints:
            - Only the latest NAVRecord (by nav_date) for the scheme is returned.
        """
        if scheme_id not in self.schemes:
            return {"success": False, "error": "Scheme does not exist"}

        navs_for_scheme = [
            nav for nav in self.nav_records.values()
            if nav["scheme_id"] == scheme_id
        ]

        if not navs_for_scheme:
            return {"success": False, "error": "No NAV records found for scheme"}

        # Assume ISO 8601 date (YYYY-MM-DD), sort descending by nav_date
        latest_nav = max(navs_for_scheme, key=lambda nav: nav["nav_date"])

        return {"success": True, "data": latest_nav}

    def get_scheme_details(self, scheme_id: str) -> dict:
        """
        Retrieve full details for a given scheme, including the scheme info,
        its associated fund house, and asset class.

        Args:
            scheme_id (str): The unique identifier for the scheme.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": {
                            "scheme": SchemeInfo,
                            "fund_house": FundHouseInfo,
                            "asset_class": AssetClassInfo
                        }
                    }
                On failure:
                    {
                        "success": False,
                        "error": str
                    }
        Constraints:
            - scheme_id must exist in self.schemes.
            - related fund_house_id and asset_class_id must exist.
        """
        scheme = self.schemes.get(scheme_id)
        if not scheme:
            return {"success": False, "error": "Scheme not found"}

        fund_house_id = scheme["fund_house_id"]
        fund_house = self.fund_houses.get(fund_house_id)
        if not fund_house:
            return {"success": False, "error": "Associated Fund House not found"}

        asset_class_id = scheme["asset_class_id"]
        asset_class = self.asset_classes.get(asset_class_id)
        if not asset_class:
            return {"success": False, "error": "Associated Asset Class not found"}

        return {
            "success": True,
            "data": {
                "scheme": scheme,
                "fund_house": fund_house,
                "asset_class": asset_class
            }
        }

    def get_asset_class_info(self, asset_class_id: str = None, name: str = None) -> dict:
        """
        Retrieve information about an asset class, given the asset_class_id or name.

        Args:
            asset_class_id (str, optional): The unique ID of the asset class.
            name (str, optional): The name of the asset class (case-insensitive).

        Returns:
            dict: 
                - On success: {"success": True, "data": AssetClassInfo}
                - On failure: {"success": False, "error": str}

        Constraints:
            - At least one of asset_class_id or name must be provided.
            - If both are provided, they must refer to the same asset class.
            - Name matches are case-insensitive.
        """
        if not asset_class_id and not name:
            return {"success": False, "error": "Must provide asset_class_id or name."}

        ac_info_by_id = None
        ac_info_by_name = None

        # Try to find by ID
        if asset_class_id:
            ac_info_by_id = self.asset_classes.get(asset_class_id)
            if not ac_info_by_id:
                return {"success": False, "error": "Asset class with given ID not found."}

        # Try to find by name (case-insensitive)
        if name:
            lower_name = name.lower()
            for ac in self.asset_classes.values():
                if ac["name"].lower() == lower_name:
                    ac_info_by_name = ac
                    break
            if not ac_info_by_name:
                return {"success": False, "error": "Asset class with given name not found."}

        # If both provided, check they refer to same asset class
        if ac_info_by_id and ac_info_by_name:
            if ac_info_by_id["asset_class_id"] != ac_info_by_name["asset_class_id"]:
                return {"success": False, "error": "asset_class_id and name refer to different asset classes."}
            return {"success": True, "data": ac_info_by_id}

        # If only one was found, return it
        if ac_info_by_id:
            return {"success": True, "data": ac_info_by_id}
        if ac_info_by_name:
            return {"success": True, "data": ac_info_by_name}

        # Should not reach here
        return {"success": False, "error": "Unknown error in retrieving asset class info."}

    def get_nav_history_for_scheme(
        self,
        scheme_id: str,
        start_date: str = None,
        end_date: str = None
    ) -> dict:
        """
        Retrieve the list of historical NAVRecords for a given scheme.

        Args:
            scheme_id (str): The scheme whose NAV history is desired.
            start_date (str, optional): (Inclusive) Lower bound for nav_date, in 'YYYY-MM-DD' ISO format.
            end_date (str, optional): (Inclusive) Upper bound for nav_date, in 'YYYY-MM-DD' ISO format.

        Returns:
            dict: {
                "success": True,
                "data": List[NAVRecordInfo] (sorted by nav_date ascending),
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints/rules:
            - scheme_id must exist.
            - If start_date/end_date provided, filter nav_records to those in the inclusive date range.
            - If no records, returns empty list with success.
            - Date filtering is lexicographical on ISO format.
        """
        if scheme_id not in self.schemes:
            return {"success": False, "error": "Scheme does not exist"}

        # Find all nav_records for this scheme
        records = [
            record for record in self.nav_records.values()
            if record['scheme_id'] == scheme_id
        ]

        # Date filtering
        if start_date is not None:
            records = [
                rec for rec in records if rec['nav_date'] >= start_date
            ]
        if end_date is not None:
            records = [
                rec for rec in records if rec['nav_date'] <= end_date
            ]

        # Sort by nav_date ascending
        records_sorted = sorted(records, key=lambda x: x['nav_date'])

        return {"success": True, "data": records_sorted}

    def add_nav_record(
        self,
        nav_record_id: str,
        scheme_id: str,
        nav_value: float,
        nav_date: str
    ) -> dict:
        """
        Add a new NAVRecord for a scheme.

        Args:
            nav_record_id (str): Unique identifier for the NAV record.
            scheme_id (str): Scheme's unique ID. Must exist in the system.
            nav_value (float): NAV value for the scheme.
            nav_date (str): Date for the NAV value, YYYY-MM-DD (ISO-8601). Must be a valid calendar date.

        Returns:
            dict: {
                "success": True,
                "message": "NAV record added for scheme <scheme_id> on date <nav_date>"
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - nav_record_id must be unique (not in self.nav_records)
            - scheme_id must exist and link to a real Scheme
            - nav_date must be a valid calendar date string (YYYY-MM-DD)
        """
        # Check nav_record_id uniqueness
        if nav_record_id in self.nav_records:
            return {"success": False, "error": "NAV record ID already exists"}

        # Check scheme_id exists
        if scheme_id not in self.schemes:
            return {"success": False, "error": "Scheme ID does not exist"}

        # Validate nav_value is float-able
        try:
            nav_value = float(nav_value)
        except (ValueError, TypeError):
            return {"success": False, "error": "NAV value must be a number"}

        # Validate date format YYYY-MM-DD and if truly a valid date
        try:
            dt = datetime.strptime(nav_date, '%Y-%m-%d')
        except ValueError:
            return {"success": False, "error": "nav_date must be a valid date in YYYY-MM-DD format"}

        # All validations passed, create the NAVRecord
        nav_record: NAVRecordInfo = {
            "nav_record_id": nav_record_id,
            "scheme_id": scheme_id,
            "nav_value": nav_value,
            "nav_date": nav_date
        }
        self.nav_records[nav_record_id] = nav_record

        return {
            "success": True,
            "message": f"NAV record added for scheme {scheme_id} on date {nav_date}"
        }

    def update_scheme_status(self, scheme_id: str, status: str) -> dict:
        """
        Change the status of a mutual fund scheme, e.g., activate or deactivate for inclusion/exclusion in default queries.

        Args:
            scheme_id (str): The identifier of the scheme to update.
            status (str): The new status for the scheme ("active" or "inactive" are standard).

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Scheme status updated to <status>" }
                On failure:
                    { "success": False, "error": "<error reason>" }

        Constraints:
            - The scheme must exist in the system.
            - Status must be one of allowed values ("active", "inactive").
              (Other statuses can be added as per system rules.)
        """
        ALLOWED_STATUSES = {"active", "inactive"}

        if scheme_id not in self.schemes:
            return {"success": False, "error": "Scheme ID does not exist"}

        if status not in ALLOWED_STATUSES:
            return {"success": False, "error": f"Invalid status value '{status}'. Allowed: {ALLOWED_STATUSES}"}

        current_status = self.schemes[scheme_id].get("status", None)
        self.schemes[scheme_id]["status"] = status

        return {"success": True, "message": f"Scheme status updated to {status}"}

    def add_scheme(
        self,
        scheme_id: str,
        name: str,
        fund_house_id: str,
        asset_class_id: str,
        launch_date: str,
        status: str
    ) -> dict:
        """
        Add a new scheme to the system, linking it to an existing fund house and asset class.

        Args:
            scheme_id (str): Unique identifier for the new scheme.
            name (str): The scheme's name.
            fund_house_id (str): ID of the fund house this scheme belongs to (must exist).
            asset_class_id (str): ID of the asset class this scheme belongs to (must exist).
            launch_date (str): Launch date in 'YYYY-MM-DD' format.
            status (str): Scheme status (e.g. 'active'/'inactive').

        Returns:
            dict: {
                "success": True,
                "message": "Scheme added successfully"
            } on success, or
            {
                "success": False,
                "error": "<reason>"
            } on failure.

        Constraints:
            - scheme_id must be unique.
            - fund_house_id and asset_class_id must refer to existing FundHouse and AssetClass.
            - All fields required (non-empty).
        """
        # Check required fields
        if not all([scheme_id, name, fund_house_id, asset_class_id, launch_date, status]):
            return {"success": False, "error": "All fields are required"}

        # Check uniqueness of scheme_id
        if scheme_id in self.schemes:
            return {"success": False, "error": "Scheme ID already exists"}

        # Check fund_house_id exists
        if fund_house_id not in self.fund_houses:
            return {"success": False, "error": "Fund house ID does not exist"}

        # Check asset_class_id exists
        if asset_class_id not in self.asset_classes:
            return {"success": False, "error": "Asset class ID does not exist"}

        # Optionally: Could validate launch_date format, but not required by spec

        # Add the new scheme
        self.schemes[scheme_id] = {
            "scheme_id": scheme_id,
            "name": name,
            "fund_house_id": fund_house_id,
            "asset_class_id": asset_class_id,
            "launch_date": launch_date,
            "status": status
        }

        return {"success": True, "message": "Scheme added successfully"}

    def update_scheme_details(
        self,
        scheme_id: str,
        name: str = None,
        asset_class_id: str = None,
        fund_house_id: str = None,
        launch_date: str = None,
        status: str = None,
    ) -> dict:
        """
        Update attributes of an existing scheme.

        Args:
            scheme_id (str): The identifier of the scheme to update.
            name (str, optional): New name for the scheme.
            asset_class_id (str, optional): New asset class ID (must exist).
            fund_house_id (str, optional): New fund house ID (must exist).
            launch_date (str, optional): New launch date for the scheme.
            status (str, optional): New status for the scheme.

        Returns:
            dict:
                - On success: { "success": True, "message": "Scheme details updated successfully" }
                - On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - The scheme must exist.
            - asset_class_id (if provided) must exist.
            - fund_house_id (if provided) must exist.
            - At least one field to update must be provided.
            - Only the allowed fields (name, asset_class_id, fund_house_id, launch_date, status) can be updated.
        """
        if scheme_id not in self.schemes:
            return { "success": False, "error": "Scheme ID does not exist" }

        if not any([name, asset_class_id, fund_house_id, launch_date, status]):
            return { "success": False, "error": "No update fields provided" }

        scheme = self.schemes[scheme_id]

        # Validate and update fields
        if asset_class_id is not None:
            if asset_class_id not in self.asset_classes:
                return { "success": False, "error": "Asset Class ID does not exist" }
            scheme['asset_class_id'] = asset_class_id

        if fund_house_id is not None:
            if fund_house_id not in self.fund_houses:
                return { "success": False, "error": "Fund House ID does not exist" }
            scheme['fund_house_id'] = fund_house_id

        if name is not None:
            scheme['name'] = name

        if launch_date is not None:
            scheme['launch_date'] = launch_date

        if status is not None:
            scheme['status'] = status

        # Save back
        self.schemes[scheme_id] = scheme

        return {
            "success": True,
            "message": "Scheme details updated successfully"
        }

    def add_fund_house(self, fund_house_id: str, name: str) -> dict:
        """
        Add a new fund house (asset management company) to the system.

        Args:
            fund_house_id (str): Unique identifier for the fund house.
            name (str): Name of the fund house.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Fund house <name> added with ID <fund_house_id>."
                    }
                On failure:
                    {
                        "success": False,
                        "error": <reason>
                    }

        Constraints:
            - fund_house_id must be unique across all fund houses.
            - Both fund_house_id and name must be non-empty.
        """
        if not fund_house_id or not isinstance(fund_house_id, str):
            return {"success": False, "error": "Invalid or missing fund_house_id"}
        if not name or not isinstance(name, str):
            return {"success": False, "error": "Invalid or missing fund house name"}
        if fund_house_id in self.fund_houses:
            return {"success": False, "error": f"Fund house with ID {fund_house_id} already exists"}

        self.fund_houses[fund_house_id] = {
            "fund_house_id": fund_house_id,
            "name": name
        }
        return {"success": True, "message": f"Fund house {name} added with ID {fund_house_id}."}

    def add_asset_class(self, asset_class_id: str, name: str, description: str) -> dict:
        """
        Add a new asset class definition to the system.

        Args:
            asset_class_id (str): Unique identifier for the asset class.
            name (str): Name of the asset class (e.g., 'equity', 'debt').
            description (str): Description of the asset class.

        Returns:
            dict: {
                "success": True,
                "message": "Asset class added successfully."
            }
            or {
                "success": False,
                "error": "Asset class ID already exists." or other validation error
            }

        Constraints:
            - asset_class_id must be unique (not already present in asset_classes).
            - All parameters must be non-empty strings.
        """
        if not asset_class_id or not name or not description:
            return {
                "success": False,
                "error": "All fields (asset_class_id, name, description) must be provided and non-empty."
            }

        if asset_class_id in self.asset_classes:
            return {
                "success": False,
                "error": "Asset class ID already exists."
            }

        asset_class_info: AssetClassInfo = {
            "asset_class_id": asset_class_id,
            "name": name,
            "description": description
        }
        self.asset_classes[asset_class_id] = asset_class_info

        return {
            "success": True,
            "message": "Asset class added successfully."
        }

    def remove_scheme(self, scheme_id: str) -> dict:
        """
        Remove (deactivate) a Scheme so it will not appear in default active queries.

        Args:
            scheme_id (str): Unique identifier for the scheme to deactivate.

        Returns:
            dict: {
                "success": True,
                "message": str   # Deactivation result,
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - Only marks the scheme as 'inactive' (does not hard-delete or remove NAV records).
            - If scheme does not exist, returns error.
            - If already inactive, operation is idempotent and still returns success.
        """
        scheme = self.schemes.get(scheme_id)
        if scheme is None:
            return {"success": False, "error": "Scheme does not exist"}

        if scheme.get("status") != "inactive":
            scheme["status"] = "inactive"
            self.schemes[scheme_id] = scheme
            return {"success": True, "message": "Scheme deactivated"}
        else:
            return {"success": True, "message": "Scheme already inactive"}

    def delete_nav_record(self, nav_record_id: str) -> dict:
        """
        Remove a specific NAVRecord from the system (administrative action).

        Args:
            nav_record_id (str): The unique identifier of the NAV record to be deleted.

        Returns:
            dict:
                - On success:
                    {"success": True, "message": "NAVRecord <nav_record_id> deleted."}
                - On failure:
                    {"success": False, "error": "<error message>"}

        Constraints:
            - NAVRecord with nav_record_id must exist in the system.
            - Deletion is an administrative action; only ensures record is removed if present.
        """
        if nav_record_id not in self.nav_records:
            return {
                "success": False,
                "error": f"NAVRecord '{nav_record_id}' does not exist."
            }
        del self.nav_records[nav_record_id]
        return {
            "success": True,
            "message": f"NAVRecord '{nav_record_id}' deleted."
        }


class MutualFundNAVTrackingSystem(BaseEnv):
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

    def get_fund_house_by_name(self, **kwargs):
        return self._call_inner_tool('get_fund_house_by_name', kwargs)

    def list_schemes_by_fund_house(self, **kwargs):
        return self._call_inner_tool('list_schemes_by_fund_house', kwargs)

    def get_scheme_by_name_and_fund_house(self, **kwargs):
        return self._call_inner_tool('get_scheme_by_name_and_fund_house', kwargs)

    def list_active_schemes_by_fund_house(self, **kwargs):
        return self._call_inner_tool('list_active_schemes_by_fund_house', kwargs)

    def get_scheme_status(self, **kwargs):
        return self._call_inner_tool('get_scheme_status', kwargs)

    def get_latest_nav_for_scheme(self, **kwargs):
        return self._call_inner_tool('get_latest_nav_for_scheme', kwargs)

    def get_scheme_details(self, **kwargs):
        return self._call_inner_tool('get_scheme_details', kwargs)

    def get_asset_class_info(self, **kwargs):
        return self._call_inner_tool('get_asset_class_info', kwargs)

    def get_nav_history_for_scheme(self, **kwargs):
        return self._call_inner_tool('get_nav_history_for_scheme', kwargs)

    def add_nav_record(self, **kwargs):
        return self._call_inner_tool('add_nav_record', kwargs)

    def update_scheme_status(self, **kwargs):
        return self._call_inner_tool('update_scheme_status', kwargs)

    def add_scheme(self, **kwargs):
        return self._call_inner_tool('add_scheme', kwargs)

    def update_scheme_details(self, **kwargs):
        return self._call_inner_tool('update_scheme_details', kwargs)

    def add_fund_house(self, **kwargs):
        return self._call_inner_tool('add_fund_house', kwargs)

    def add_asset_class(self, **kwargs):
        return self._call_inner_tool('add_asset_class', kwargs)

    def remove_scheme(self, **kwargs):
        return self._call_inner_tool('remove_scheme', kwargs)

    def delete_nav_record(self, **kwargs):
        return self._call_inner_tool('delete_nav_record', kwargs)

