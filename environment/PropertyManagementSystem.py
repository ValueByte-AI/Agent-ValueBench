# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict, Optional
from typing import List, Dict, Any



class PropertyInfo(TypedDict):
    property_id: str
    address: str
    type: str
    status: str
    owner_id: str
    lease_id: Optional[str]
    maintenance_id: Optional[str]

class OwnerInfo(TypedDict):
    owner_id: str
    name: str
    contact_info: str

class LeaseInfo(TypedDict):
    lease_id: str
    property_id: str
    tenant_name: str
    start_date: str
    end_date: str
    lease_sta: str  # Status of the lease

class MaintenanceRecordInfo(TypedDict):
    maintenance_id: str
    property_id: str
    description: str
    date_requested: str
    date_completed: Optional[str]
    sta: str  # Status of the maintenance record

class _GeneratedEnvImpl:
    def __init__(self):
        # Properties: {property_id: PropertyInfo}
        self.properties: Dict[str, PropertyInfo] = {}

        # Owners: {owner_id: OwnerInfo}
        self.owners: Dict[str, OwnerInfo] = {}

        # Leases: {lease_id: LeaseInfo}
        self.leases: Dict[str, LeaseInfo] = {}

        # Maintenance Records: {maintenance_id: MaintenanceRecordInfo}
        self.maintenance_records: Dict[str, MaintenanceRecordInfo] = {}

        # --- Constraints ---
        # - property_id must be unique for each property
        # - Each property must be associated with a valid owner (owner_id exists)
        # - A property can have zero or one active lease at any time
        # - Maintenance records must reference valid property_id
        # - Property status must be one of predefined states

    def get_property_by_id(self, property_id: str) -> dict:
        """
        Retrieve full property details by given property_id.

        Args:
            property_id (str): The unique identifier for the property.

        Returns:
            dict: {
                "success": True,
                "data": PropertyInfo  # Complete property information
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g., 'Property not found'
            }

        Constraints:
            - property_id must exist in the system.
        """
        if not isinstance(property_id, str) or not property_id:
            return { "success": False, "error": "Invalid property_id" }

        prop = self.properties.get(property_id)
        if prop is None:
            return { "success": False, "error": "Property not found" }
    
        return { "success": True, "data": prop }


    def get_properties_by_ids(self, property_ids: List[str]) -> dict:
        """
        Retrieve the PropertyInfo details for each property in the provided list of property_ids.

        Args:
            property_ids (List[str]): List of property IDs to search for.

        Returns:
            dict: {
                "success": True,
                "data": List[PropertyInfo],   # List of info for found properties (empty if none found)
            }
            or
            {
                "success": False,
                "error": str  # Error message, e.g., if bad input
            }

        Constraints / Handling:
            - Only returns data for property_ids found in the system.
            - If property_ids is not a list of strings, returns error.
            - If input list is empty, returns success with empty data list.
        """
        if not isinstance(property_ids, list):
            return { "success": False, "error": "property_ids must be a list" }
        if not all(isinstance(pid, str) for pid in property_ids):
            return { "success": False, "error": "Each property_id must be a string" }
    
        result = [
            self.properties[pid]
            for pid in property_ids
            if pid in self.properties
        ]
        return { "success": True, "data": result }

    def list_all_properties(self) -> dict:
        """
        List all properties currently stored in the property management system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[PropertyInfo]  # List of all properties, may be empty if none exist
            }

        Constraints:
            - No input needed.
            - Returns all properties as-is.
        """
        all_properties = list(self.properties.values())
        return { "success": True, "data": all_properties }

    def get_owner_by_id(self, owner_id: str) -> dict:
        """
        Retrieve owner details given an owner_id.

        Args:
            owner_id (str): The unique identifier of the property owner.

        Returns:
            dict:
                On success:
                    { "success": True, "data": OwnerInfo }
                On failure:
                    { "success": False, "error": "Owner not found" }

        Constraints:
            - The owner_id must exist in the system (self.owners).
        """
        owner = self.owners.get(owner_id)
        if owner is None:
            return { "success": False, "error": "Owner not found" }
        return { "success": True, "data": owner }

    def get_property_owner(self, property_id: str) -> dict:
        """
        Fetch the owner details associated with a given property_id.

        Args:
            property_id (str): Unique identifier for the property.

        Returns:
            dict: {
                "success": True,
                "data": OwnerInfo  # Owner details associated with property
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (property or owner not found)
            }

        Constraints:
            - property_id must exist in the system.
            - The property must reference a valid owner_id present in self.owners.
        """
        property_info = self.properties.get(property_id)
        if property_info is None:
            return { "success": False, "error": "Property not found" }

        owner_id = property_info.get("owner_id")
        owner_info = self.owners.get(owner_id)
        if owner_info is None:
            return { "success": False, "error": "Owner not found for property" }

        return { "success": True, "data": owner_info }

    def get_lease_by_id(self, lease_id: str) -> dict:
        """
        Retrieve lease details for a given lease_id.

        Args:
            lease_id (str): Unique identifier for the lease.

        Returns:
            dict:
                - On success:
                    { "success": True, "data": LeaseInfo }
                - On failure:
                    { "success": False, "error": "Lease not found" }

        Constraints:
            - lease_id must exist in the system.
        """
        lease = self.leases.get(lease_id)
        if lease is None:
            return { "success": False, "error": "Lease not found" }
        return { "success": True, "data": lease }

    def get_property_lease(self, property_id: str) -> dict:
        """
        Given a property_id, fetch the associated lease details (if any).

        Args:
            property_id (str): The unique identifier of the property.

        Returns:
            dict:
                - If property not found:
                    { "success": False, "error": "Property not found" }
                - If property found but no associated lease:
                    { "success": True, "data": None }
                - If property and lease found:
                    { "success": True, "data": LeaseInfo }
                - If lease_id is set but lease record missing:
                    { "success": False, "error": "Lease record not found" }
        Constraints:
            - property_id must exist in the system.
            - Each property can have zero or one lease (tracked via lease_id).
        """
        prop = self.properties.get(property_id)
        if not prop:
            return {"success": False, "error": "Property not found"}
        lease_id = prop.get("lease_id")
        if not lease_id:
            return {"success": True, "data": None}
        lease = self.leases.get(lease_id)
        if not lease:
            return {"success": False, "error": "Lease record not found"}
        return {"success": True, "data": lease}

    def get_maintenance_by_id(self, maintenance_id: str) -> dict:
        """
        Retrieve the maintenance record details for a given maintenance_id.

        Args:
            maintenance_id (str): The unique identifier of the maintenance record.

        Returns:
            dict:
                - On success:
                    {"success": True, "data": MaintenanceRecordInfo}
                - On failure:
                    {"success": False, "error": str} (if maintenance_id not found)

        Constraints:
            - maintenance_id must reference an existing maintenance record.
        """
        record = self.maintenance_records.get(maintenance_id)
        if record is None:
            return { "success": False, "error": "Maintenance record not found for the given maintenance_id." }
        return { "success": True, "data": record }

    def get_property_maintenance_records(self, property_id: str) -> dict:
        """
        Retrieve all maintenance records associated with the given property_id.

        Args:
            property_id (str): Unique identifier for the property.

        Returns:
            dict: {
                "success": True,
                "data": List[MaintenanceRecordInfo]  # List of maintenance records (empty if none found)
            }
            or
            {
                "success": False,
                "error": str  # Error message if property not found
            }

        Constraints:
            - property_id must exist in the system.
            - Only returns maintenance records referencing the given property_id.
        """
        if property_id not in self.properties:
            return {"success": False, "error": "Property with this ID does not exist."}

        records = [
            record for record in self.maintenance_records.values()
            if record["property_id"] == property_id
        ]
        return {"success": True, "data": records}

    def list_properties_by_status(self, status: str) -> dict:
        """
        List all properties filtered by a specific status.

        Args:
            status (str): The desired property status to filter (e.g., 'available', 'leased', 'under maintenance').

        Returns:
            dict: {
                "success": True,
                "data": List[PropertyInfo]  # matching properties
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., invalid status)
            }

        Constraints:
            - status must be one of the predefined valid property states.
        """
        valid_statuses = {"available", "leased", "under maintenance", "sold", "pending"}
        if status not in valid_statuses:
            return {"success": False, "error": f"Invalid status '{status}'. Must be one of {sorted(valid_statuses)}"}

        filtered = [
            prop for prop in self.properties.values()
            if prop["status"] == status
        ]
        return {"success": True, "data": filtered}

    def check_property_validity(self, property_id: str) -> dict:
        """
        Confirm that a property has a unique property_id and is associated with a valid owner.

        Args:
            property_id (str): Unique identifier for the property to check.

        Returns:
            dict:
                - success: True
                - data: {
                      "valid": bool,      # Whether property is valid (unique property_id and valid owner)
                      "reason": str       # Reason for invalidity (if any)
                  }
                OR
                - success: False
                - error: str            # Reason for query failure (e.g., property does not exist)

        Constraints:
            - property_id must be unique (enforced by dict keys).
            - owner_id for property must exist in owners.
        """
        # Check if property exists
        property_info = self.properties.get(property_id)
        if property_info is None:
            return {"success": False, "error": "Property does not exist"}

        owner_id = property_info.get("owner_id")
        if not owner_id or owner_id not in self.owners:
            return {
                "success": True,
                "data": {
                    "valid": False,
                    "reason": "Invalid or missing owner"
                }
            }

        # Property id uniqueness is guaranteed by dict structure
        return {
            "success": True,
            "data": {
                "valid": True,
                "reason": "Property ID is unique and has valid owner"
            }
        }

    def add_property(
        self,
        property_id: str,
        address: str,
        type: str,
        status: str,
        owner_id: str,
        lease_id: Optional[str] = None,
        maintenance_id: Optional[str] = None
    ) -> dict:
        """
        Add a new property to the management system.

        Args:
            property_id (str): Unique identifier for the property.
            address (str): Address of the property.
            type (str): Type of the property (e.g., apartment, house).
            status (str): Current status (must be in predefined states).
            owner_id (str): Owner's unique identifier (must exist).
            lease_id (Optional[str]): Associated lease ID. Omit it when there is no linked lease yet.
            maintenance_id (Optional[str]): Associated maintenance ID. Omit it when there is no linked maintenance record yet.

        Returns:
            dict: 
            - On success: {"success": True, "message": "Property <property_id> added successfully."}
            - On failure: {"success": False, "error": "reason"}

        Constraints:
            - property_id must be unique.
            - owner_id must already be present in the system.
            - status must be one of allowed states.
        """
        # Allowed property statuses (example, adjust as needed)
        allowed_statuses = {"available", "leased", "under maintenance", "sold", "pending"}

        if property_id in self.properties:
            return {"success": False, "error": "Property ID already exists."}

        if owner_id not in self.owners:
            return {"success": False, "error": "Owner ID does not exist."}

        if status not in allowed_statuses:
            return {"success": False, "error": f"Invalid property status '{status}'. Allowed: {', '.join(allowed_statuses)}"}

        # Construct property info
        property_info: PropertyInfo = {
            "property_id": property_id,
            "address": address,
            "type": type,
            "status": status,
            "owner_id": owner_id,
            "lease_id": lease_id,
            "maintenance_id": maintenance_id
        }

        self.properties[property_id] = property_info

        return {"success": True, "message": f"Property {property_id} added successfully."}

    def update_property(
        self, 
        property_id: str, 
        updates: dict
    ) -> dict:
        """
        Modify existing property information for a given property_id.

        Args:
            property_id (str): The unique identifier of the property to update.
            updates (dict): Fields/values to update for the property. Valid keys are:
                address, type, status, owner_id, lease_id, maintenance_id.

        Returns:
            dict: {
                "success": True,
                "message": "Property updated successfully"
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - property_id must exist.
            - If owner_id is updated, new owner_id must exist.
            - If lease_id is updated, new lease_id must exist.
            - If maintenance_id is updated, new maintenance_id must exist.
            - If status is updated, it must be in allowed property statuses.
            - property_id itself cannot be changed.
        """
        allowed_statuses = {"available", "leased", "under maintenance", "sold", "pending"}

        if property_id not in self.properties:
            return { "success": False, "error": "Property does not exist" }

        prop = self.properties[property_id]

        # Field validation
        if "owner_id" in updates:
            new_owner_id = updates["owner_id"]
            if new_owner_id not in self.owners:
                return { "success": False, "error": "New owner_id does not exist" }
            prop["owner_id"] = new_owner_id

        if "lease_id" in updates:
            new_lease_id = updates["lease_id"]
            if new_lease_id is not None and new_lease_id not in self.leases:
                return { "success": False, "error": "New lease_id does not exist" }
            prop["lease_id"] = new_lease_id

        if "maintenance_id" in updates:
            new_maintenance_id = updates["maintenance_id"]
            if new_maintenance_id is not None and new_maintenance_id not in self.maintenance_records:
                return { "success": False, "error": "New maintenance_id does not exist" }
            prop["maintenance_id"] = new_maintenance_id

        if "status" in updates:
            new_status = updates["status"]
            if new_status not in allowed_statuses:
                return { "success": False, "error": f"Invalid status: {new_status}" }
            prop["status"] = new_status

        # Allow simple updates for address and type
        if "address" in updates:
            prop["address"] = updates["address"]
        if "type" in updates:
            prop["type"] = updates["type"]

        # Commit the update (dict is mutable, so already in self.properties)
        return { "success": True, "message": "Property updated successfully" }

    def delete_property(self, property_id: str) -> dict:
        """
        Remove a property record from the system by its property_id.

        Args:
            property_id (str): Unique identifier of the property to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Property deleted successfully."
            }
            or
            {
                "success": False,
                "error": "Property not found."
            }

        Constraints:
            - Property must exist.
            - Only the property record is removed; related leases or maintenance records, if any, are not affected.
        """
        if property_id not in self.properties:
            return {"success": False, "error": "Property not found."}

        del self.properties[property_id]
        return {"success": True, "message": "Property deleted successfully."}

    def add_owner(self, owner_id: str, name: str, contact_info: str) -> dict:
        """
        Create a new owner entry in the system.

        Args:
            owner_id (str): Unique identifier for the owner.
            name (str): Name of the owner.
            contact_info (str): Contact information for the owner.

        Returns:
            dict: {
                "success": True,
                "message": str  # Success message if owner added
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. duplicate owner_id
            }

        Constraints:
            - owner_id must be unique; if owner_id already exists, operation fails.
            - All parameters must be provided.
        """
        if not owner_id or not name or not contact_info:
            return {
                "success": False,
                "error": "Missing required owner information."
            }

        if owner_id in self.owners:
            return {
                "success": False,
                "error": f"Owner ID '{owner_id}' already exists."
            }

        self.owners[owner_id] = {
            "owner_id": owner_id,
            "name": name,
            "contact_info": contact_info
        }
        return {
            "success": True,
            "message": f"Owner '{owner_id}' added successfully."
        }

    def update_owner(self, owner_id: str, name: Optional[str] = None, contact_info: Optional[str] = None) -> dict:
        """
        Edit owner details associated with a specific owner_id.

        Args:
            owner_id (str): The unique identifier of the owner to update.
            name (Optional[str]): New name for the owner (optional).
            contact_info (Optional[str]): New contact info for the owner (optional).

        Returns:
            dict: {
                "success": True,
                "message": str  # Success message
            }
            or
            {
                "success": False,
                "error": str  # Description of the error
            }

        Constraints:
            - owner_id must exist in the system.
            - Only 'name' and 'contact_info' can be updated.
        """
        if owner_id not in self.owners:
            return { "success": False, "error": "Owner ID not found" }
    
        owner = self.owners[owner_id]

        updated_fields = []
        if name is not None:
            owner["name"] = name
            updated_fields.append("name")
        if contact_info is not None:
            owner["contact_info"] = contact_info
            updated_fields.append("contact_info")

        # Update the record in the dictionary
        self.owners[owner_id] = owner

        if updated_fields:
            message = f"Owner details updated: {', '.join(updated_fields)} for owner_id {owner_id}"
        else:
            message = f"No changes made for owner_id {owner_id}"

        return { "success": True, "message": message }

    def add_lease(
        self,
        lease_id: str,
        property_id: str,
        tenant_name: str,
        start_date: str,
        end_date: str,
        lease_sta: str
    ) -> dict:
        """
        Add a new lease and associate it with a property, ensuring that the property has no active lease.

        Args:
            lease_id (str): Unique identifier for the new lease.
            property_id (str): The property to associate with this lease.
            tenant_name (str): The name of the tenant.
            start_date (str): Lease start date.
            end_date (str): Lease end date.
            lease_sta (str): The status of the lease (typically 'active').

        Returns:
            dict: Success or error message.

        Constraints:
            - lease_id must not exist.
            - property_id must exist.
            - Property must not already have an active lease.
            - lease_sta is stored as provided.
            - Updates both the leases and property's lease mapping.
        """
        # Check lease_id uniqueness
        if lease_id in self.leases:
            return {"success": False, "error": "Lease ID already exists."}
        # Check property exists
        if property_id not in self.properties:
            return {"success": False, "error": "Property does not exist."}
        # Check property lease status
        prop_info = self.properties[property_id]
        cur_lease_id = prop_info.get('lease_id')
        if cur_lease_id is not None:
            # lease_id exists: check whether current lease is active
            cur_lease = self.leases.get(cur_lease_id)
            if cur_lease and cur_lease.get('lease_sta', '').lower() == 'active':
                return {"success": False, "error": "Property already has an active lease."}
        # Add lease
        lease_info = {
            "lease_id": lease_id,
            "property_id": property_id,
            "tenant_name": tenant_name,
            "start_date": start_date,
            "end_date": end_date,
            "lease_sta": lease_sta
        }
        self.leases[lease_id] = lease_info
        # Associate lease with property
        self.properties[property_id]['lease_id'] = lease_id
        return {"success": True, "message": "Lease added and associated with property."}

    def update_lease(
        self,
        lease_id: str,
        tenant_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        lease_sta: Optional[str] = None
    ) -> dict:
        """
        Update lease details for a given lease_id. Allows modifying tenant_name, start_date, end_date, and lease_sta.

        Args:
            lease_id (str): Identifier for the lease to update.
            tenant_name (Optional[str]): Updated tenant name.
            start_date (Optional[str]): Updated lease start date (ISO format recommended).
            end_date (Optional[str]): Updated lease end date.
            lease_sta (Optional[str]): Updated lease status.

        Returns:
            dict:
                - success: True if update was performed, False if error.
                - message: Description of successful operation.
                - error: If failed, description of the error.

        Constraints:
            - lease_id must exist in the system.
            - At least one update field must be provided.
            - Lease status, if provided, must be a valid status (enforced here only if relevant statuses are known).
            - Lease property_id must remain valid.
        """
        # Check lease existence
        if lease_id not in self.leases:
            return {"success": False, "error": "Lease does not exist."}

        lease_info = self.leases[lease_id]
        updated_fields = 0

        # Update fields if provided
        if tenant_name is not None:
            lease_info['tenant_name'] = tenant_name
            updated_fields += 1

        if start_date is not None:
            lease_info['start_date'] = start_date
            updated_fields += 1

        if end_date is not None:
            lease_info['end_date'] = end_date
            updated_fields += 1

        if lease_sta is not None:
            lease_info['lease_sta'] = lease_sta
            updated_fields += 1

        if updated_fields == 0:
            return {"success": False, "error": "No update fields provided."}

        # Constraint: Lease property_id must remain valid
        property_id = lease_info.get("property_id")
        if property_id is None or property_id not in self.properties:
            return {"success": False, "error": "Lease references invalid property."}

        # Optionally, enforce valid lease status values
        allowed_statuses = {"active", "terminated", "inactive", "pending"}
        if lease_sta is not None and lease_sta not in allowed_statuses:
            return {"success": False, "error": f"Invalid lease status '{lease_sta}'."}

        # Enforce one active lease per property
        if lease_sta is not None and lease_sta == "active":
            for other_id, other_lease in self.leases.items():
                if other_id != lease_id and other_lease["property_id"] == property_id and other_lease["lease_sta"] == "active":
                    return {"success": False, "error": "Another active lease exists for this property."}

        # If lease status is set to inactive or terminated, clear lease_id from property record
        if lease_sta is not None and lease_sta in {"terminated", "inactive"}:
            property_info = self.properties[property_id]
            if property_info.get("lease_id") == lease_id:
                property_info["lease_id"] = None

        # Save updated lease
        self.leases[lease_id] = lease_info

        return {"success": True, "message": "Lease updated successfully."}

    def terminate_lease(self, lease_id: str) -> dict:
        """
        End an active lease and update the associated property state.

        Args:
            lease_id (str): The unique identifier of the lease to be terminated.
    
        Returns:
            dict: {
                "success": True,
                "message": str  # Description of action taken
            }
            or
            {
                "success": False,
                "error": str  # Error description
            }
    
        Constraints:
            - Lease must exist and be active.
            - Lease must reference a valid property.
            - Property status updated to "available" after lease termination.
            - Lease status set to "terminated".
        """
        # 1. Check for lease existence
        lease = self.leases.get(lease_id)
        if not lease:
            return { "success": False, "error": "Lease does not exist." }

        # 2. Check lease is active (assuming 'active' is the status for active leases)
        if lease["lease_sta"] != "active":
            return { "success": False, "error": "Lease is not active and cannot be terminated." }

        property_id = lease.get("property_id")
        property_info = self.properties.get(property_id)
        if not property_info:
            return { "success": False, "error": "Associated property does not exist." }
    
        # 3. Terminate the lease
        lease["lease_sta"] = "terminated"
        # Optionally, could set lease["end_date"] to current date (not required here)

        # 4. Update the property: clear lease_id and set status to "available"
        property_info["lease_id"] = None
        property_info["status"] = "available"

        # 5. Save changes (already operates on references inside dicts)

        return {
            "success": True,
            "message": f"Lease {lease_id} terminated and property {property_id} is now available."
        }

    def add_maintenance_record(
        self,
        maintenance_id: str,
        property_id: str,
        description: str,
        date_requested: str,
        sta: str,
        date_completed: Optional[str] = None
    ) -> dict:
        """
        Add a new maintenance record for a given property.

        Args:
            maintenance_id (str): Unique ID for the maintenance record.
            property_id (str): Existing property ID this maintenance is for.
            description (str): Description of the maintenance request.
            date_requested (str): Date when maintenance was requested.
            date_completed (Optional[str]): Date when maintenance was completed. Omit it while the work is still pending.
            sta (str): Status of the maintenance record.

        Returns:
            dict: {
                "success": True,
                "message": "Maintenance record added successfully."
            }
            or
            {
                "success": False,
                "error": Reason for failure.
            }

        Constraints:
            - maintenance_id must be unique.
            - property_id must exist in the managed properties.
        """
        if not maintenance_id:
            return {"success": False, "error": "Maintenance ID cannot be empty."}
        if maintenance_id in self.maintenance_records:
            return {"success": False, "error": "Maintenance ID already exists."}
        if not property_id:
            return {"success": False, "error": "Property ID cannot be empty."}
        if property_id not in self.properties:
            return {"success": False, "error": "Property ID does not exist."}

        # Create maintenance record entry
        record: MaintenanceRecordInfo = {
            "maintenance_id": maintenance_id,
            "property_id": property_id,
            "description": description,
            "date_requested": date_requested,
            "date_completed": date_completed,
            "sta": sta
        }
        self.maintenance_records[maintenance_id] = record
        return {
            "success": True,
            "message": "Maintenance record added successfully."
        }

    def update_maintenance_record(
        self,
        maintenance_id: str,
        description: Optional[str] = None,
        date_requested: Optional[str] = None,
        date_completed: Optional[str] = None,
        sta: Optional[str] = None,
        property_id: Optional[str] = None
    ) -> dict:
        """
        Update details or status of an existing maintenance record.

        Args:
            maintenance_id (str): ID of the maintenance record to update.
            description (Optional[str]): New description.
            date_requested (Optional[str]): Updated request date.
            date_completed (Optional[str]): Updated completion date. Omit it if no completion date should be changed.
            sta (Optional[str]): Updated status.
            property_id (Optional[str]): Updated referenced property ID.

        Returns:
            dict: {
                "success": True,
                "message": "Maintenance record updated successfully."
            }
            or
            {
                "success": False,
                "error": "Reason for failure"
            }

        Constraints:
            - maintenance_id must reference a valid record.
            - If property_id is changed, it must reference a valid property.
            - (Optional) Status must be valid if strict enforcement.
        """
        if maintenance_id not in self.maintenance_records:
            return {"success": False, "error": "Maintenance record does not exist."}

        record = self.maintenance_records[maintenance_id]

        if property_id is not None:
            if property_id not in self.properties:
                return {"success": False, "error": "Invalid property_id; property does not exist."}
            record["property_id"] = property_id

        if description is not None:
            record["description"] = description

        if date_requested is not None:
            record["date_requested"] = date_requested

        if date_completed is not None:
            record["date_completed"] = date_completed

        if sta is not None:
            # Optional: Validate against allowed status values.
            record["sta"] = sta

        # Save back (dict is mutable, but ensure consistency)
        self.maintenance_records[maintenance_id] = record

        return {"success": True, "message": "Maintenance record updated successfully."}

    def delete_maintenance_record(self, maintenance_id: str) -> dict:
        """
        Remove a maintenance record from the system.

        Args:
            maintenance_id (str): The unique identifier of the maintenance record to delete.

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
            - maintenance_id must exist in the system.
            - Remove any references from Property.maintenance_id that point to this record (set to None).
        """
        if maintenance_id not in self.maintenance_records:
            return { "success": False, "error": "Maintenance record not found." }

        # Remove reference from properties, if any
        for property_info in self.properties.values():
            if property_info.get("maintenance_id") == maintenance_id:
                property_info["maintenance_id"] = None

        del self.maintenance_records[maintenance_id]
        return {
            "success": True,
            "message": f"Maintenance record {maintenance_id} deleted."
        }


class PropertyManagementSystem(BaseEnv):
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

    def get_property_by_id(self, **kwargs):
        return self._call_inner_tool('get_property_by_id', kwargs)

    def get_properties_by_ids(self, **kwargs):
        return self._call_inner_tool('get_properties_by_ids', kwargs)

    def list_all_properties(self, **kwargs):
        return self._call_inner_tool('list_all_properties', kwargs)

    def get_owner_by_id(self, **kwargs):
        return self._call_inner_tool('get_owner_by_id', kwargs)

    def get_property_owner(self, **kwargs):
        return self._call_inner_tool('get_property_owner', kwargs)

    def get_lease_by_id(self, **kwargs):
        return self._call_inner_tool('get_lease_by_id', kwargs)

    def get_property_lease(self, **kwargs):
        return self._call_inner_tool('get_property_lease', kwargs)

    def get_maintenance_by_id(self, **kwargs):
        return self._call_inner_tool('get_maintenance_by_id', kwargs)

    def get_property_maintenance_records(self, **kwargs):
        return self._call_inner_tool('get_property_maintenance_records', kwargs)

    def list_properties_by_status(self, **kwargs):
        return self._call_inner_tool('list_properties_by_status', kwargs)

    def check_property_validity(self, **kwargs):
        return self._call_inner_tool('check_property_validity', kwargs)

    def add_property(self, **kwargs):
        return self._call_inner_tool('add_property', kwargs)

    def update_property(self, **kwargs):
        return self._call_inner_tool('update_property', kwargs)

    def delete_property(self, **kwargs):
        return self._call_inner_tool('delete_property', kwargs)

    def add_owner(self, **kwargs):
        return self._call_inner_tool('add_owner', kwargs)

    def update_owner(self, **kwargs):
        return self._call_inner_tool('update_owner', kwargs)

    def add_lease(self, **kwargs):
        return self._call_inner_tool('add_lease', kwargs)

    def update_lease(self, **kwargs):
        return self._call_inner_tool('update_lease', kwargs)

    def terminate_lease(self, **kwargs):
        return self._call_inner_tool('terminate_lease', kwargs)

    def add_maintenance_record(self, **kwargs):
        return self._call_inner_tool('add_maintenance_record', kwargs)

    def update_maintenance_record(self, **kwargs):
        return self._call_inner_tool('update_maintenance_record', kwargs)

    def delete_maintenance_record(self, **kwargs):
        return self._call_inner_tool('delete_maintenance_record', kwargs)
