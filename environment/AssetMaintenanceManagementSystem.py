# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict
from datetime import datetime
from typing import Optional, Dict, Any
import uuid



class FacilityInfo(TypedDict):
    facility_id: str
    name: str
    location: str
    contact_info: str

class AssetInfo(TypedDict):
    asset_id: str
    type: str
    facility_id: str
    status: str
    install_date: str
    serial_num: str

class MaintenanceScheduleInfo(TypedDict):
    schedule_id: str
    asset_id: str
    scheduled_date: str
    recurrence_pattern: str
    last_maintenance_date: str
    next_maintenance_date: str
    status: str

class MaintenanceHistoryInfo(TypedDict):
    history_id: str
    asset_id: str
    maintenance_date: str
    performed_by: str
    notes: str
    outcome: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Facilities: {facility_id: FacilityInfo}
        self.facilities: Dict[str, FacilityInfo] = {}
        # Assets: {asset_id: AssetInfo}
        self.assets: Dict[str, AssetInfo] = {}
        # Maintenance Schedules: {schedule_id: MaintenanceScheduleInfo}
        self.maintenance_schedules: Dict[str, MaintenanceScheduleInfo] = {}
        # Maintenance Histories: {history_id: MaintenanceHistoryInfo}
        self.maintenance_histories: Dict[str, MaintenanceHistoryInfo] = {}

        # Constraints:
        # - Each asset must be assigned to one facility (Asset.facility_id ∈ facilities)
        # - Maintenance schedules must be associated with a specific asset (MaintenanceSchedule.asset_id ∈ assets)
        # - Only assets with a valid and active status are eligible for future maintenance scheduling
        # - MaintenanceHistory entries must refer to assets that exist in the system (MaintenanceHistory.asset_id ∈ assets)

    def get_facility_by_name(self, name: str) -> dict:
        """
        Retrieve facility information for a facility matching the given name.

        Args:
            name (str): The facility's name to search for.

        Returns:
            dict:
                - On success: {"success": True, "data": FacilityInfo}
                - On error (not found): {"success": False, "error": "Facility not found"}

        Constraints:
            - Facility names are assumed to be unique; if not, the first match will be returned.
        """
        for facility_info in self.facilities.values():
            if facility_info.get("name") == name:
                return { "success": True, "data": facility_info }
        return { "success": False, "error": "Facility not found" }

    def get_facility_by_id(self, facility_id: str) -> dict:
        """
        Retrieve facility information given a facility_id.

        Args:
            facility_id (str): The unique identifier for the facility.

        Returns:
            dict: {
                "success": True,
                "data": FacilityInfo
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - facility_id must exist in the facilities database.
        """
        if facility_id in self.facilities:
            return {
                "success": True,
                "data": self.facilities[facility_id]
            }
        else:
            return {
                "success": False,
                "error": "Facility not found"
            }

    def list_facilities(self) -> dict:
        """
        List all facilities in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[FacilityInfo]  # List of all facilities (may be empty if none exist)
            }
        Constraints:
            - None specific; returns current state of self.facilities.
        """
        facilities_list = list(self.facilities.values())
        return { "success": True, "data": facilities_list }

    def get_assets_by_facility(self, facility_id: str) -> dict:
        """
        List all assets assigned to a specific facility.

        Args:
            facility_id (str): The unique identifier for the facility.

        Returns:
            dict: 
                - On success: {"success": True, "data": [AssetInfo, ...]}
                - On failure: {"success": False, "error": "Facility does not exist"}

        Constraints:
            - The facility must exist in the system.
            - All assets returned have asset['facility_id'] == facility_id.
        """
        if facility_id not in self.facilities:
            return {"success": False, "error": "Facility does not exist"}

        assets_list = [
            asset for asset in self.assets.values()
            if asset["facility_id"] == facility_id
        ]

        return {"success": True, "data": assets_list}

    def get_assets_by_type(self, asset_type: str) -> dict:
        """
        Retrieve all assets of the given type.

        Args:
            asset_type (str): The type of asset to filter for (e.g., 'scale', 'HVAC').

        Returns:
            dict: {
                "success": True,
                "data": List[AssetInfo]  # List of assets matching the type (empty if none found)
            }
            or
            {
                "success": False,
                "error": str  # Description of the error
            }

        Constraints:
            - asset_type must be provided (not None or empty).
        """
        if not asset_type:
            return { "success": False, "error": "Asset type must be provided." }

        results = [
            asset for asset in self.assets.values()
            if asset['type'] == asset_type
        ]

        return { "success": True, "data": results }

    def get_asset_by_id(self, asset_id: str) -> dict:
        """
        Fetch detailed information for a specific asset by its unique asset_id.

        Args:
            asset_id (str): The unique ID of the asset to query.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "data": AssetInfo  # Asset info dictionary.
                    }
                - On failure (not found):
                    {
                        "success": False,
                        "error": "Asset not found"
                    }
        """
        asset = self.assets.get(asset_id)
        if asset is None:
            return { "success": False, "error": "Asset not found" }
        return { "success": True, "data": asset }

    def get_assets_by_status(self, status: str) -> dict:
        """
        Fetch all assets filtered by their status (e.g., 'active', 'inactive', 'out-of-service').

        Args:
            status (str): The target asset status to filter on.

        Returns:
            dict: {
                'success': True,
                'data': List[AssetInfo]  # All assets with the given status (empty list if none found)
            }
            or
            {
                'success': False,
                'error': str  # Reason for failure (e.g., invalid input)
            }
    
        Constraints:
            - No asset state is changed.
            - Status comparison is case-sensitive.
            - Returns empty list if no assets match; that is not an error.
        """
        if not isinstance(status, str) or not status.strip():
            return {"success": False, "error": "Invalid status specified"}

        result = [
            asset_info for asset_info in self.assets.values()
            if asset_info.get("status") == status
        ]
        return {"success": True, "data": result}

    def get_eligible_assets_for_maintenance(self) -> dict:
        """
        Retrieve all assets that are:
          - assigned to a valid facility (facility_id in self.facilities), AND
          - have a status of 'active'
        These assets are eligible for future maintenance scheduling.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[AssetInfo]
            }

        Constraints:
            - Only assets with status 'active' are eligible.
            - Asset must be assigned to a facility that exists in the system.
        """
        eligible_assets = []
        for asset in self.assets.values():
            if asset["status"] == "active" and asset["facility_id"] in self.facilities:
                eligible_assets.append(asset)
        return { "success": True, "data": eligible_assets }

    def get_maintenance_schedules_by_asset(self, asset_id: str) -> dict:
        """
        Retrieve all maintenance schedules associated with a given asset.

        Args:
            asset_id (str): The ID of the asset to retrieve maintenance schedules for.

        Returns:
            dict: 
                - { "success": True, "data": List[MaintenanceScheduleInfo] }
                  (Empty list if none exist for the asset)
                - { "success": False, "error": str } if the asset does not exist.

        Constraints:
            - asset_id must exist in the system.
        """
        if asset_id not in self.assets:
            return { "success": False, "error": "Asset does not exist" }

        schedules = [
            sched for sched in self.maintenance_schedules.values()
            if sched["asset_id"] == asset_id
        ]
        return { "success": True, "data": schedules }


    def get_next_maintenance_schedule_for_asset(self, asset_id: str) -> Dict[str, Any]:
        """
        Retrieve the next upcoming (future) maintenance schedule for the given asset.

        Args:
            asset_id (str): The unique identifier of the asset.

        Returns:
            dict:
              - On success and schedule found:
                {
                    "success": True,
                    "data": MaintenanceScheduleInfo  # Dict with the next schedule for this asset
                }
              - On success but no upcoming schedules:
                {
                    "success": True,
                    "data": None
                }
              - On error:
                {
                    "success": False,
                    "error": str  # Reason for failure
                }

        Constraints:
            - The asset must exist in the system.
            - Only shows schedules for this asset that are in the future (scheduled_date or next_maintenance_date > now).
            - Returns the schedule with the soonest future scheduled_date (or next_maintenance_date).
        """
        if asset_id not in self.assets:
            return { "success": False, "error": "Asset does not exist" }

        now = datetime.now()
        # Collect all schedules for this asset whose scheduled_date or next_maintenance_date > now
        schedules = []
        for sched in self.maintenance_schedules.values():
            if sched.get("asset_id") != asset_id:
                continue

            # Parse scheduled_date and next_maintenance_date, fallback to scheduled_date if next_maintenance_date is absent
            try:
                sched_date_str = sched.get("next_maintenance_date") or sched.get("scheduled_date")
                sched_date = datetime.fromisoformat(sched_date_str)
            except Exception:
                # date parsing error, skip this schedule
                continue

            if sched_date > now:
                schedules.append( (sched_date, sched) )

        # No upcoming maintenance schedules
        if not schedules:
            return { "success": True, "data": None }

        # Pick the soonest upcoming schedule
        schedules.sort(key=lambda tup: tup[0])
        next_schedule = schedules[0][1]
        return { "success": True, "data": next_schedule }

    def get_assets_by_facility_and_type(self, facility_id: str, asset_type: str) -> dict:
        """
        Retrieve all assets of a certain type at a specific facility.

        Args:
            facility_id (str): The unique identifier of the facility.
            asset_type (str): The type/category of asset to retrieve.

        Returns:
            dict:
                On success:
                    {"success": True, "data": List[AssetInfo]}  # List may be empty if no match
                On error:
                    {"success": False, "error": str}
    
        Constraints:
            - The facility_id must exist in the system.
        """
        if facility_id not in self.facilities:
            return {"success": False, "error": "Facility does not exist"}

        assets = [
            asset for asset in self.assets.values()
            if asset["facility_id"] == facility_id and asset["type"] == asset_type
        ]
        return {"success": True, "data": assets}

    def get_maintenance_history_by_asset(self, asset_id: str) -> dict:
        """
        Retrieve all maintenance history records for the specified asset.

        Args:
            asset_id (str): The ID of the asset for which history is requested.

        Returns:
            dict: {
                "success": True,
                "data": List[MaintenanceHistoryInfo]  # List may be empty if no history exists
            }
            or
            {
                "success": False,
                "error": str  # e.g. asset does not exist
            }

        Constraints:
            - The asset_id must exist in the system (must be present in self.assets).
        """
        if asset_id not in self.assets:
            return { "success": False, "error": "Asset does not exist" }

        histories = [
            history for history in self.maintenance_histories.values()
            if history["asset_id"] == asset_id
        ]
        return { "success": True, "data": histories }

    def add_asset(
        self,
        asset_id: str,
        type: str,
        facility_id: str,
        status: str,
        install_date: str,
        serial_num: str
    ) -> dict:
        """
        Register a new asset and assign it to a facility.

        Args:
            asset_id (str): Unique ID for the asset (must not already exist).
            type (str): Type/category of the asset.
            facility_id (str): The facility to which the asset will be assigned (must exist).
            status (str): The status of the asset (e.g., 'active', 'inactive').
            install_date (str): Date asset was installed (ISO or other standard format).
            serial_num (str): Serial number of the asset.

        Returns:
            dict: {
                "success": True,
                "message": str
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - asset_id must be unique
            - facility_id must exist in the system
        """
        # Check asset_id uniqueness
        if asset_id in self.assets:
            return {
                "success": False,
                "error": f"Asset ID '{asset_id}' already exists."
            }

        # Check that the facility exists
        if facility_id not in self.facilities:
            return {
                "success": False,
                "error": f"Facility ID '{facility_id}' does not exist."
            }

        # Register the new asset
        self.assets[asset_id] = {
            "asset_id": asset_id,
            "type": type,
            "facility_id": facility_id,
            "status": status,
            "install_date": install_date,
            "serial_num": serial_num
        }

        return {
            "success": True,
            "message": f"Asset '{asset_id}' has been added and assigned to facility '{facility_id}'."
        }

    def update_asset_status(self, asset_id: str, new_status: str) -> dict:
        """
        Change the status of an asset (e.g., mark as active, inactive, retired, etc.).

        Args:
            asset_id (str): The ID of the asset to update.
            new_status (str): The new status to apply to the asset.

        Returns:
            dict:
                - On success: {"success": True, "message": "Asset status updated successfully."}
                - On failure: {"success": False, "error": "<reason>"}

        Constraints:
            - Asset must exist in the system (asset_id in self.assets).
        """
        asset = self.assets.get(asset_id)
        if not asset:
            return {"success": False, "error": "Asset not found."}

        asset["status"] = new_status
        return {"success": True, "message": "Asset status updated successfully."}

    def assign_asset_to_facility(self, asset_id: str, facility_id: str) -> dict:
        """
        Move or reassign an asset to a different facility.

        Args:
            asset_id (str): The ID of the asset to reassign.
            facility_id (str): The ID of the facility to assign the asset to.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Asset <asset_id> assigned to facility <facility_id>" }
                On failure:
                    { "success": False, "error": <description> }

        Constraints:
            - Asset must exist in the system.
            - Facility must exist in the system.
            - Each asset must be assigned to exactly one facility after the operation.
        """
        # Check if asset exists
        if asset_id not in self.assets:
            return {"success": False, "error": "Asset does not exist"}

        # Check if facility exists
        if facility_id not in self.facilities:
            return {"success": False, "error": "Facility does not exist"}

        # Update asset's facility_id
        self.assets[asset_id]["facility_id"] = facility_id

        return {
            "success": True,
            "message": f"Asset {asset_id} assigned to facility {facility_id}"
        }


    def schedule_maintenance_for_asset(
        self,
        asset_id: str,
        scheduled_date: str,
        recurrence_pattern: str,
        status: str,
        last_maintenance_date: str = "",
        next_maintenance_date: str = "",
        schedule_id: str = ""
    ) -> dict:
        """
        Create a new maintenance schedule entry for an asset.

        Args:
            asset_id (str): Asset ID to schedule maintenance for. Must exist and be active/eligible.
            scheduled_date (str): Date for scheduled maintenance (ISO 8601 string or agreed format).
            recurrence_pattern (str): Recurrence rule/pattern (e.g., 'monthly').
            status (str): Status of the schedule (e.g. 'scheduled').
            last_maintenance_date (str, optional): Last maintenance date (may be empty for new).
            next_maintenance_date (str, optional): Next maintenance date (computed or given).
            schedule_id (str, optional): Provide to override/generated if omitted.

        Returns:
            dict: {
                "success": True,
                "message": "Maintenance schedule created",
                "schedule_id": <id>,
            }
            or {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - asset_id must be present in self.assets and have an 'active' status (or otherwise eligible).
            - schedule_id must not already exist.
            - All required fields must be provided.
        """
        # Check asset existence
        asset = self.assets.get(asset_id)
        if not asset:
            return { "success": False, "error": "Asset does not exist" }

        # Only allow eligible (active) assets
        if asset.get("status", "").lower() != "active":
            return { "success": False, "error": "Asset is not eligible for maintenance scheduling" }

        # Generate unique schedule_id if not provided
        if not schedule_id:
            schedule_id = str(uuid.uuid4())
        else:
            if schedule_id in self.maintenance_schedules:
                return { "success": False, "error": "Schedule ID already exists" }

        # Create the maintenance schedule entry
        schedule_entry = {
            "schedule_id": schedule_id,
            "asset_id": asset_id,
            "scheduled_date": scheduled_date,
            "recurrence_pattern": recurrence_pattern,
            "last_maintenance_date": last_maintenance_date,
            "next_maintenance_date": next_maintenance_date,
            "status": status
        }

        self.maintenance_schedules[schedule_id] = schedule_entry

        return {
            "success": True,
            "message": "Maintenance schedule created",
            "schedule_id": schedule_id
        }

    def update_maintenance_schedule(
        self,
        schedule_id: str,
        scheduled_date: str = None,
        recurrence_pattern: str = None,
        last_maintenance_date: str = None,
        next_maintenance_date: str = None,
        status: str = None
    ) -> dict:
        """
        Modifies the timing or recurrence details of an existing maintenance schedule.
    
        Args:
            schedule_id (str): The ID of the maintenance schedule to update.
            scheduled_date (str, optional): New scheduled maintenance date.
            recurrence_pattern (str, optional): New schedule recurrence pattern.
            last_maintenance_date (str, optional): New last maintenance date.
            next_maintenance_date (str, optional): New next scheduled date.
            status (str, optional): New status for the schedule.

        Returns:
            dict: {
                "success": True,
                "message": "Maintenance schedule updated successfully."
            } on success, or
            {
                "success": False,
                "error": <reason>
            } on failure.

        Constraints:
            - Schedule must exist.
            - Associated asset must exist.
            - If next_maintenance_date or scheduled_date is provided, the associated asset must have an 'active' status.
            - At least one field to update must be provided.
        """

        # Ensure the schedule exists
        if schedule_id not in self.maintenance_schedules:
            return {"success": False, "error": "Maintenance schedule does not exist."}

        schedule = self.maintenance_schedules[schedule_id]
        asset_id = schedule["asset_id"]

        # Ensure the associated asset exists
        if asset_id not in self.assets:
            return {"success": False, "error": "Associated asset does not exist."}

        asset = self.assets[asset_id]

        # If scheduling to the future, ensure asset is eligible (status "active" or "valid")
        status_ok = asset["status"].lower() in ("active", "valid")
        if ((scheduled_date or next_maintenance_date) and not status_ok):
            return {"success": False, "error": "Asset is not eligible for future maintenance scheduling."}

        # Ensure at least one update field is provided
        if not any([scheduled_date, recurrence_pattern, last_maintenance_date, next_maintenance_date, status]):
            return {"success": False, "error": "No update parameters provided."}

        # Update fields if provided
        if scheduled_date is not None:
            schedule["scheduled_date"] = scheduled_date
        if recurrence_pattern is not None:
            schedule["recurrence_pattern"] = recurrence_pattern
        if last_maintenance_date is not None:
            schedule["last_maintenance_date"] = last_maintenance_date
        if next_maintenance_date is not None:
            schedule["next_maintenance_date"] = next_maintenance_date
        if status is not None:
            schedule["status"] = status

        self.maintenance_schedules[schedule_id] = schedule

        return {"success": True, "message": "Maintenance schedule updated successfully."}

    def add_maintenance_history_entry(
        self,
        history_id: str,
        asset_id: str,
        maintenance_date: str,
        performed_by: str,
        notes: str,
        outcome: str
    ) -> dict:
        """
        Record a recently performed maintenance event in maintenance history.

        Args:
            history_id (str): Unique identifier for the maintenance history record.
            asset_id (str): The asset this maintenance was performed on; asset must exist.
            maintenance_date (str): Date of maintenance (format assumed to be valid).
            performed_by (str): Persone/role who performed maintenance.
            notes (str): Maintenance details.
            outcome (str): Result of the maintenance.

        Returns:
            dict: 
                On success: { "success": True, "message": "Maintenance history entry recorded." }
                On failure: { "success": False, "error": <reason> }

        Constraints:
          - asset_id must exist in the system.
          - history_id must be unique.
        """
        if not history_id or not asset_id or not maintenance_date or not performed_by or not outcome:
            return {"success": False, "error": "Missing required maintenance history fields."}

        if asset_id not in self.assets:
            return {"success": False, "error": "Asset does not exist."}

        if history_id in self.maintenance_histories:
            return {"success": False, "error": "History ID already exists."}

        entry = {
            "history_id": history_id,
            "asset_id": asset_id,
            "maintenance_date": maintenance_date,
            "performed_by": performed_by,
            "notes": notes,
            "outcome": outcome
        }
        self.maintenance_histories[history_id] = entry
        return {"success": True, "message": "Maintenance history entry recorded."}

    def remove_asset(self, asset_id: str) -> dict:
        """
        Remove an asset identified by asset_id, subject to business logic:
          - Asset must exist.
          - Asset cannot be removed if it is referenced by maintenance schedules or histories.
    
        Args:
            asset_id (str): The asset's unique identifier.

        Returns:
            dict: {
                "success": True,
                "message": "Asset <asset_id> removed successfully."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - Cannot remove asset if referenced in MaintenanceSchedule or MaintenanceHistory.
        """
        if asset_id not in self.assets:
            return {"success": False, "error": "Asset not found"}

        # Check Maintenance Schedules for references
        for sched in self.maintenance_schedules.values():
            if sched["asset_id"] == asset_id:
                return {
                    "success": False,
                    "error": f"Cannot remove asset; referenced by maintenance schedule {sched['schedule_id']}"
                }

        # Check Maintenance History for references
        for hist in self.maintenance_histories.values():
            if hist["asset_id"] == asset_id:
                return {
                    "success": False,
                    "error": f"Cannot remove asset; referenced by maintenance history {hist['history_id']}"
                }

        del self.assets[asset_id]
        return {
            "success": True,
            "message": f"Asset {asset_id} removed successfully."
        }

    def remove_maintenance_schedule(self, schedule_id: str) -> dict:
        """
        Delete a scheduled maintenance entry from the system.

        Args:
            schedule_id (str): The identifier of the maintenance schedule to delete.

        Returns:
            dict:
                On success: { "success": True, "message": "Maintenance schedule removed successfully" }
                On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - The schedule_id must exist in the system.
            - Removal does NOT cascade to maintenance history or assets (no additional changes).
        """
        if schedule_id not in self.maintenance_schedules:
            return { "success": False, "error": "Maintenance schedule not found" }
    
        del self.maintenance_schedules[schedule_id]
        return { "success": True, "message": "Maintenance schedule removed successfully" }

    def update_facility_info(
        self,
        facility_id: str,
        name: str = None,
        location: str = None,
        contact_info: str = None
    ) -> dict:
        """
        Edit facility details: name, location, and/or contact_info.

        Args:
            facility_id (str): ID of the facility to update.
            name (str, optional): New facility name (if updating).
            location (str, optional): New location (if updating).
            contact_info (str, optional): New contact info (if updating).

        Returns:
            dict:
                - On success:
                    {"success": True, "message": "Facility info updated"}
                - On failure:
                    {"success": False, "error": <reason>}

        Constraints:
            - Facility must exist.
            - At least one field (name, location, contact_info) must be provided for update.
        """
        facility = self.facilities.get(facility_id)
        if not facility:
            return {"success": False, "error": "Facility does not exist"}

        fields_to_update = {}
        if name is not None:
            fields_to_update["name"] = name
        if location is not None:
            fields_to_update["location"] = location
        if contact_info is not None:
            fields_to_update["contact_info"] = contact_info

        if not fields_to_update:
            return {"success": False, "error": "No update fields provided"}

        for key, value in fields_to_update.items():
            facility[key] = value

        self.facilities[facility_id] = facility
        return {"success": True, "message": "Facility info updated"}

    def add_facility(
        self,
        facility_id: str,
        name: str,
        location: str,
        contact_info: str
    ) -> dict:
        """
        Register a new facility in the system.
    
        Args:
            facility_id (str): Unique identifier for the facility.
            name (str): Facility name.
            location (str): Physical location.
            contact_info (str): Contact information.
        
        Returns:
            dict: {
                "success": True,
                "message": "Facility [facility_id] added successfully"
            }
            or
            {
                "success": False,
                "error": "error reason"
            }

        Constraints:
            - facility_id must not already exist in self.facilities
            - All fields must be non-empty strings
        """
        if not all([facility_id, name, location, contact_info]):
            return {"success": False, "error": "All fields are required and must be non-empty"}

        if facility_id in self.facilities:
            return {"success": False, "error": f"Facility '{facility_id}' already exists"}

        self.facilities[facility_id] = {
            "facility_id": facility_id,
            "name": name,
            "location": location,
            "contact_info": contact_info
        }
        return {"success": True, "message": f"Facility '{facility_id}' added successfully"}

    def remove_facility(self, facility_id: str) -> dict:
        """
        Delete a facility by its ID, only if no assets are assigned to it.

        Args:
            facility_id (str): Identifier of the facility to remove.

        Returns:
            dict: If success:
                {
                    "success": True,
                    "message": "Facility <facility_id> removed successfully."
                }
                If failure:
                {
                    "success": False,
                    "error": "<reason>"
                }

        Constraints:
            - Facility must exist.
            - Must have no assets assigned to this facility.
            - No cascading deletes.
        """
        # Check facility existence
        if facility_id not in self.facilities:
            return {"success": False, "error": f"Facility {facility_id} does not exist."}

        # Check if any asset is assigned to this facility
        assigned_assets = [
            asset for asset in self.assets.values()
            if asset['facility_id'] == facility_id
        ]
        if assigned_assets:
            return {
                "success": False,
                "error": f"Cannot remove facility {facility_id}: assets are assigned to this facility."
            }

        # Remove facility
        del self.facilities[facility_id]
        return {
            "success": True,
            "message": f"Facility {facility_id} removed successfully."
        }


class AssetMaintenanceManagementSystem(BaseEnv):
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

    def get_facility_by_name(self, **kwargs):
        return self._call_inner_tool('get_facility_by_name', kwargs)

    def get_facility_by_id(self, **kwargs):
        return self._call_inner_tool('get_facility_by_id', kwargs)

    def list_facilities(self, **kwargs):
        return self._call_inner_tool('list_facilities', kwargs)

    def get_assets_by_facility(self, **kwargs):
        return self._call_inner_tool('get_assets_by_facility', kwargs)

    def get_assets_by_type(self, **kwargs):
        return self._call_inner_tool('get_assets_by_type', kwargs)

    def get_asset_by_id(self, **kwargs):
        return self._call_inner_tool('get_asset_by_id', kwargs)

    def get_assets_by_status(self, **kwargs):
        return self._call_inner_tool('get_assets_by_status', kwargs)

    def get_eligible_assets_for_maintenance(self, **kwargs):
        return self._call_inner_tool('get_eligible_assets_for_maintenance', kwargs)

    def get_maintenance_schedules_by_asset(self, **kwargs):
        return self._call_inner_tool('get_maintenance_schedules_by_asset', kwargs)

    def get_next_maintenance_schedule_for_asset(self, **kwargs):
        return self._call_inner_tool('get_next_maintenance_schedule_for_asset', kwargs)

    def get_assets_by_facility_and_type(self, **kwargs):
        return self._call_inner_tool('get_assets_by_facility_and_type', kwargs)

    def get_maintenance_history_by_asset(self, **kwargs):
        return self._call_inner_tool('get_maintenance_history_by_asset', kwargs)

    def add_asset(self, **kwargs):
        return self._call_inner_tool('add_asset', kwargs)

    def update_asset_status(self, **kwargs):
        return self._call_inner_tool('update_asset_status', kwargs)

    def assign_asset_to_facility(self, **kwargs):
        return self._call_inner_tool('assign_asset_to_facility', kwargs)

    def schedule_maintenance_for_asset(self, **kwargs):
        return self._call_inner_tool('schedule_maintenance_for_asset', kwargs)

    def update_maintenance_schedule(self, **kwargs):
        return self._call_inner_tool('update_maintenance_schedule', kwargs)

    def add_maintenance_history_entry(self, **kwargs):
        return self._call_inner_tool('add_maintenance_history_entry', kwargs)

    def remove_asset(self, **kwargs):
        return self._call_inner_tool('remove_asset', kwargs)

    def remove_maintenance_schedule(self, **kwargs):
        return self._call_inner_tool('remove_maintenance_schedule', kwargs)

    def update_facility_info(self, **kwargs):
        return self._call_inner_tool('update_facility_info', kwargs)

    def add_facility(self, **kwargs):
        return self._call_inner_tool('add_facility', kwargs)

    def remove_facility(self, **kwargs):
        return self._call_inner_tool('remove_facility', kwargs)

